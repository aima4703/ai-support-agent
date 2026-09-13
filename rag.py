"""
This is a simplified RAG (Retrieval-Augmented Generation) system.

The core RAG idea, in plain words:
1. Break documents into small chunks (paragraphs)
2. Turn every chunk into a list of numbers (a "vector") that captures
   what it's about
3. When a question comes in, turn IT into a vector too
4. Find which chunk's vector is most similar to the question's vector
5. Hand that chunk's actual text to the AI as context, so it answers
   using real company policy instead of guessing

This version uses TF-IDF (from scikit-learn, which you already know)
instead of neural embeddings — it's simpler, needs no extra downloads
or API calls, and is enough to demonstrate the concept solidly.
A natural upgrade later is swapping this for HuggingFace embeddings
+ a real vector database like pgvector or ChromaDB, same as PolicyBot.
"""

import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

POLICIES_FOLDER = os.path.join(os.path.dirname(__file__), "policies")


def _load_chunks():
    """Reads every .txt file in policies/ and splits it into paragraphs."""
    chunks = []
    sources = []

    for filepath in glob.glob(os.path.join(POLICIES_FOLDER, "*.txt")):
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Split on blank lines so each paragraph becomes its own chunk.
        # Skip very short chunks (like a lone title) so they don't
        # accidentally "win" a match over the real content.
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in paragraphs:
            if len(p.split()) < 5:
                continue
            chunks.append(p)
            sources.append(filename)

    return chunks, sources


# Build the index ONCE when the app starts, not on every question.
# This is the "vector database" in miniature: a list of chunks + a
# matrix of their TF-IDF vectors, kept in memory.
_chunks, _sources = _load_chunks()
_vectorizer = TfidfVectorizer(stop_words="english")
_chunk_vectors = _vectorizer.fit_transform(_chunks)


def search_policies(query: str, top_k: int = 3) -> list[dict]:
    """
    Given a question, returns the top_k most relevant policy chunks.
    """
    query_vector = _vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, _chunk_vectors)[0]

    # Get the indices of the best-matching chunks, best first
    best_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for i in best_indices:
        results.append(
            {
                "source": _sources[i],
                "text": _chunks[i],
                "relevance_score": round(float(similarities[i]), 3),
            }
        )
    return results
