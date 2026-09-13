"""
This is the upgraded RAG system: real embeddings + a real vector
database, replacing the earlier TF-IDF version (kept as
rag_tfidf_backup.py for reference).

What changed and why, in plain words:

- TF-IDF (the old version) matches based on shared WORDS. It doesn't
  understand meaning — "cost" and "price" look unrelated to it.
- This version uses a neural embedding model (the same family of
  HuggingFace embeddings you used in PolicyBot) that converts each
  chunk of text into a list of numbers capturing its MEANING. Two
  sentences with similar meaning end up with similar numbers, even
  if they don't share any exact words.
- Instead of keeping those numbers in memory (like the TF-IDF
  version did), they're now stored in PostgreSQL using the pgvector
  extension — a real vector database, the same category of tool as
  ChromaDB, just built into Postgres instead of being separate.

The overall RAG idea is unchanged: chunk documents -> embed them ->
find the closest match to a question -> hand that to the AI as
context. Only the "how do we measure similarity, and where do we
store it" parts got upgraded.
"""

import os
import glob
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://raguser:ragpass@localhost:5432/policies"
)
POLICIES_FOLDER = os.path.join(os.path.dirname(__file__), "policies")

# This model turns text into a list of 384 numbers (its "embedding").
# It downloads once (~90MB) the first time and is cached after that.
print("Loading embedding model (first run may take a moment)...")
_model = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = 384


def _get_raw_connection():
    """A plain connection, with no vector type registered yet.
    Needed the very first time, before the pgvector extension exists."""
    return psycopg2.connect(DATABASE_URL)


def _get_connection():
    """A connection that knows how to send/receive vector values.
    Only safe to use AFTER the pgvector extension has been created."""
    conn = _get_raw_connection()
    register_vector(conn)
    return conn


def _ensure_table():
    """Creates the pgvector extension and table if they don't exist yet.

    Important: this uses a RAW connection (not _get_connection), because
    register_vector() requires the 'vector' type to already exist in the
    database — and the very first time this runs, it doesn't yet. We
    create the extension first, then everything after this function can
    safely use _get_connection().
    """
    conn = _get_raw_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS policy_chunks (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding vector({EMBEDDING_DIM})
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def _load_chunks_from_files():
    """Same chunking logic as before: read .txt files, split into paragraphs."""
    chunks = []
    sources = []

    for filepath in glob.glob(os.path.join(POLICIES_FOLDER, "*.txt")):
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in paragraphs:
            if len(p.split()) < 5:  # skip lone titles/headers
                continue
            chunks.append(p)
            sources.append(filename)

    return chunks, sources


def _index_is_empty() -> bool:
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM policy_chunks;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count == 0


def _build_index():
    """Embeds every policy chunk and stores it in pgvector. Runs once."""
    chunks, sources = _load_chunks_from_files()
    embeddings = _model.encode(chunks, normalize_embeddings=True)

    conn = _get_connection()
    cur = conn.cursor()
    for text, source, embedding in zip(chunks, sources, embeddings):
        cur.execute(
            "INSERT INTO policy_chunks (source, chunk_text, embedding) VALUES (%s, %s, %s)",
            (source, text, embedding),
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Indexed {len(chunks)} policy chunks into pgvector.")


# Set up the table and fill it with embeddings ONCE when the app
# starts, if it's not already populated. This mirrors what seed.py
# does for your orders table.
_ensure_table()
if _index_is_empty():
    _build_index()
else:
    print("Policy index already populated — skipping re-embedding.")


def search_policies(query: str, top_k: int = 3) -> list[dict]:
    """
    Given a question, returns the top_k most relevant policy chunks
    using REAL semantic similarity (embeddings), not keyword overlap.
    """
    query_embedding = _model.encode([query], normalize_embeddings=True)[0]

    conn = _get_connection()
    cur = conn.cursor()
    # The <=> operator is pgvector's cosine DISTANCE (smaller = more
    # similar), so we order by it ascending and convert to a
    # similarity score (1 - distance) just for display purposes.
    cur.execute(
        """
        SELECT source, chunk_text, 1 - (embedding <=> %s) AS similarity
        FROM policy_chunks
        ORDER BY embedding <=> %s
        LIMIT %s;
        """,
        (query_embedding, query_embedding, top_k),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"source": row[0], "text": row[1], "relevance_score": round(float(row[2]), 3)}
        for row in rows
    ]
