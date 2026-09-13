# 🤖 AI Support Agent

An AI-powered customer support agent for an online store — it doesn't just chat, it **takes real actions**: looking up live order data and searching real company policy documents using semantic search, instead of guessing.

Built end-to-end as a hands-on learning project: from a plain FastAPI backend, through tool-calling AI agents, real RAG with a vector database, graph-based agent orchestration, and full Docker containerization.

*(See [BUILD_LOG.md](BUILD_LOG.md) for the step-by-step journey this was built in, including the real bugs hit and fixed along the way.)*

---

## ✨ What it does

- **Order tracking** — "Where is my order #4582?" → looks up the real order in PostgreSQL/SQLite and replies with live status, product, and delivery date
- **Policy Q&A (semantic RAG)** — "What happens if my package shows up broken?" → finds the right policy passage using *meaning*, not just keyword matching (this phrase shares no words with the actual policy text, yet it correctly retrieves the refund policy)
- **Honest about limits** — if an order doesn't exist, it says so — it never invents order details or policy rules
- **Natural conversation** — handles greetings and small talk normally, without forcing a tool call every time

The AI decides, per message, whether it needs a tool — and if so, which one — through an explicit LangGraph agent graph.

---

## 🧠 Architecture

```
User message
     │
     ▼
FastAPI  /chat  endpoint
     │
     ▼
┌─────────────────────────────────────────┐
│           LangGraph agent graph          │
│                                           │
│   START ──► [agent] ──(needs a tool?)──► [tools]
│                │                              │
│                │◄─────────────────────────────┘
│                ▼
│              END (final answer)
└─────────────────────────────────────────┘
     │
     ├── lookup_order(order_id)  ───────► PostgreSQL/SQLite (orders)
     │
     └── search_policy(query)   ───────► pgvector (semantic search over
                                           embedded policy documents)
     │
     ▼
Natural-language reply, grounded in real data
     │
     ▼
Custom chat UI
```

This is a real (if intentionally scoped-down) example of **graph-based agent orchestration**: an LLM reasons over user intent, calls the right tool with the right arguments via an explicit state graph, and grounds its final answer in what the tool actually returned.

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Orders database | SQLAlchemy + SQLite |
| Agent orchestration | **LangGraph** (explicit graph: agent node ↔ tools node) |
| LLM | Groq API (`openai/gpt-oss-120b`) via `langchain-groq` |
| RAG — embeddings | HuggingFace `sentence-transformers` (`all-MiniLM-L6-v2`) |
| RAG — vector store | **PostgreSQL + pgvector** (real semantic similarity search) |
| Containerization | **Docker** + Docker Compose (2 services: app + Postgres) |
| Frontend | Vanilla HTML/CSS/JavaScript, custom-designed (no framework) |

---

## 📂 Project structure

```
support_agent/
├── main.py                   # FastAPI app: routes for /, /health, /orders/{id}, /chat
├── database.py                # SQLAlchemy connection setup (orders DB)
├── models.py                   # Customer & Order table definitions
├── seed.py                      # Populates the orders database with sample data
├── tools.py                      # Plain functions the AI can call (lookup_order, search_policy)
├── chat.py                        # LangGraph agent: builds the graph, runs the conversation
├── chat_manual_backup.py           # Earlier hand-rolled tool-calling loop (kept for comparison)
├── rag.py                           # Embeds policy docs + queries pgvector for semantic search
├── rag_tfidf_backup.py               # Earlier TF-IDF version of RAG (kept for comparison)
├── policies/                          # Return / shipping / refund policy text files
├── static/index.html                   # The chat UI
├── Dockerfile                           # Builds the app image (CPU-only PyTorch, no GPU bloat)
├── docker-compose.yml                    # Runs the app + a pgvector-enabled Postgres together
├── requirements.txt
└── .env.example                           # Template for your Groq API key
```

---

## 🚀 Running it

**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) and a free [Groq API key](https://console.groq.com/keys).

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd support_agent
   ```

2. **Add your Groq API key**

   Copy `.env.example` to `.env` and fill in your key:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```

3. **Build and run everything** (app + Postgres, in one command)
   ```bash
   docker compose up --build
   ```
   First run takes a few minutes (downloading dependencies + the embedding model). Subsequent runs are fast.

4. **Open the app**

   Go to [http://localhost:8000](http://localhost:8000) and try:
   - *"where is my order 4582?"*
   - *"what happens if my package shows up broken?"*
   - *"how much does shipping cost?"*

---

## 🎯 What this project demonstrates

- Designing **AI tools/functions** so an LLM takes grounded actions instead of hallucinating
- **Graph-based agent orchestration** with LangGraph (state graphs, conditional routing, tool nodes)
- A real **RAG pipeline** with actual embeddings and a production-grade vector store (pgvector), not just keyword search
- **Containerized, multi-service deployment** with Docker Compose
- End-to-end ownership: database → agent logic → vector search → API → UI
- Real debugging across the stack: Docker networking issues, database connection ordering bugs, and LLM tool-naming quirks — see [BUILD_LOG.md](BUILD_LOG.md) for the actual troubleshooting process

---

## 🔭 Possible next steps

- Deploy it live (Render, Railway, Fly.io) for a shareable public link
- Extend the LangGraph graph into true multiple specialist agents (a Supervisor node routing to separate Order and Policy agent nodes)
- Add observability/tracing (Langfuse or LangSmith)
- Swap SQLite for PostgreSQL for the orders table too, for a single unified database


