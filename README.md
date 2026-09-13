# AI Support Agent — Step 1: Order Lookup

This is the first building block of the AI Customer Support Agent project.
No AI yet — just a working backend with a real database, so the foundation
is solid before we add the smart parts.

## What this does

- Stores customers and orders in a database
- Lets you look up an order by ID and get its status back

## How to run it

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Fill the database with some fake test data:
   ```
   python seed.py
   ```

3. Start the server:
   ```
   uvicorn main:app --reload
   ```

4. Open your browser to:
   ```
   http://127.0.0.1:8000/docs
   ```
   This gives you an interactive page where you can try the endpoints
   without writing any code.

5. Try looking up order `4582`, `4583`, or `4584` (these come from
   `seed.py`). Try a number that doesn't exist too, like `9999`, to see
   the "not found" response.

## Files in this step

| File | What it's for |
|---|---|
| `database.py` | Connects to the database (SQLite for now — easy to switch to Postgres later) |
| `models.py` | Defines the `Customer` and `Order` tables |
| `seed.py` | Fills the database with fake test data |
| `main.py` | The actual API — this is what runs |

## Step 2: AI Chat (new!)

Now there's a `/chat` endpoint. Type a plain-English question and the
AI decides on its own whether it needs to look up an order.

### Setup

1. Copy `.env.example` to a new file called `.env`
2. Get a free Groq API key from https://console.groq.com/keys
3. Paste it into `.env` so it looks like:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
4. Install the new dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Restart the server:
   ```
   uvicorn main:app --reload
   ```
6. Go to http://127.0.0.1:8000/docs, open **POST /chat**, click
   "Try it out", and send:
   ```
   { "message": "where is my order 4582?" }
   ```

### New files in this step

| File | What it's for |
|---|---|
| `tools.py` | The order-lookup function, plus a description of it that the AI can understand |
| `chat.py` | Sends your message to Groq, lets it decide whether to use the tool, and gets back a natural-language answer |
| `.env.example` | Template for your API key — copy it to `.env` and fill in your real key |

## What's next (Step 3)

Add RAG: feed the AI a couple of policy documents (return policy,
shipping policy) so it can answer questions like "can I return this
after 20 days?" using real company rules instead of guessing.

## Step 3: RAG for policy questions (new!)

The AI can now answer questions about returns, refunds, and shipping
by actually searching real policy documents instead of guessing.

### What's new

- `policies/` folder — three plain-text policy documents (you can add
  your own or edit these)
- `rag.py` — splits those documents into paragraphs and finds the
  most relevant ones for any question (this is the "R" in RAG:
  Retrieval)
- `tools.py` — now has a second tool, `search_policy`, that the AI
  can call
- `chat.py` — updated so the AI knows it has two tools now, and knows
  to use `search_policy` for policy questions

### How this version of RAG works (simplified)

Real RAG systems (like your PolicyBot) use AI-generated embeddings
and a vector database (ChromaDB, pgvector, etc). To keep this step
lighter, this version uses TF-IDF (from scikit-learn) instead — it
measures word overlap rather than true meaning, so it's less
powerful, but needs no extra downloads or API calls, and teaches the
same core idea: **break documents into chunks → find the most
relevant chunk for a question → give that chunk to the AI as
context.**

A natural next upgrade (not required, just an idea for later) is
swapping `rag.py` to use HuggingFace embeddings and a real vector
database, the same combo you used in PolicyBot.

### Try it

Restart the server (`uvicorn main:app --reload`) and send:
```
{ "message": "can I return an item after 20 days?" }
{ "message": "how much does shipping cost?" }
{ "message": "my order arrived damaged, what do I do?" }
```

### New/changed files in this step

| File | What it's for |
|---|---|
| `policies/*.txt` | The actual policy documents to search |
| `rag.py` | Splits documents into chunks and finds the best match for a question |
| `tools.py` | Now also describes the `search_policy` tool to the AI |
| `chat.py` | Now routes to whichever tool the AI picks |

## What's next (Step 4)

Wrap this up with a simple chat page (HTML/JS) so you can demo it in
a browser instead of the `/docs` page, then push the whole thing to
GitHub with a clear README.

## Step 4: A real chat page (new!)

Now there's an actual webpage to demo instead of the `/docs` page.

### What's new

- `static/index.html` — a single self-contained chat page (HTML +
  CSS + JavaScript all in one file, no build tools needed)
- `main.py` — now has a route for `/` that serves this page

### Try it

1. Restart the server:
   ```
   uvicorn main:app --reload
   ```
2. Open your browser to:
   ```
   http://127.0.0.1:8000
   ```
   (no `/docs` needed this time — this IS the app)
3. Type a message and hit Send or press Enter

### How it works, simply

The page's JavaScript sends whatever you type to your `/chat`
endpoint (the exact same one you tested in `/docs`) using `fetch()`,
then shows the reply as a chat bubble. It's the same AI agent from
Steps 2-3 — just with a proper front door instead of the developer
docs page.

## What's next (Step 5 — optional / for later)

The project is now a fully working, demoable AI agent. If you want
to keep going for your portfolio:
- Push it to GitHub with a clear README (screenshot of the chat UI
  goes a long way)
- Record a short demo video/gif
- Optionally add: Docker (for deployment), a proper vector database
  (pgvector or ChromaDB) instead of TF-IDF, or LangGraph if you want
  to show multi-agent orchestration explicitly

None of those are required — what you have right now is already a
complete, working, three-skill project (tool-calling AI agent + RAG
+ real database) that's genuinely demoable.
