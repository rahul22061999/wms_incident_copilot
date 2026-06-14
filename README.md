# WMS Incident Copilot API

[![CI](https://github.com/rahuluk9632/wms-incident-api/actions/workflows/ci.yml/badge.svg)](https://github.com/rahuluk9632/wms-incident-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A multi-agent AI backend that diagnoses warehouse incidents. You describe a problem — pick failures, inventory discrepancies, inbound delays — and the system figures out what's wrong by querying your WMS database and searching your SOP documentation, then returns a structured diagnosis with a root cause, confidence score, and citations.

---

## How it works

When a ticket comes in, an LLM router reads the description and decides whether the investigation needs parallel lookups (e.g. check inventory AND order status at the same time) or a sequential deep-dive (where one result informs the next query). The system runs whichever path fits, pulls evidence from SQL and SOPs, and a synthesizer node merges everything into a single grounded response.

You can also ask it to monitor a ticket on a recurring schedule — it'll re-run the full investigation every N minutes and push updates over a live SSE stream.

```
POST /v1/tickets/
        │
        ▼
   FastAPI + JWT
        │
        ▼
 diagnose_ticket_service  (semaphore: max 10 concurrent)
        │
        ▼
┌────────────────────────────────────────────────┐
│               LangGraph StateGraph             │
│                                                │
│  router ──► parallel planner ──► SQL + SOP    │
│         └─► sequential agent (ReAct loop)     │
│         └─► schedule / cancel                 │
│                      │                        │
│                 synthesizer                   │
└────────────────────────────────────────────────┘
        │
        ▼
  structured JSON diagnosis + citations
```

---

## Running it with Docker

This is the fastest way to get everything running. Docker handles Postgres, Qdrant, the API, and the scheduler — one command starts it all.

### 1. Clone the repo

```bash
git clone https://github.com/rahuluk9632/wms-incident-api.git
cd wms-incident-api
```

### 2. Create your `.env` file

```bash
# create the file and fill in your keys
cat > .env << 'EOF'
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...
OLLAMA_API_KEY=any-string-if-not-using-ollama
LANGSMITH_API_KEY=...

# your actual WMS postgres database (read-only access is enough)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/wms_db

# these stay as-is for the docker setup
MEMORIES_DB_URL=sqlite+aiosqlite:///./audit.db
JOB_SCHEDULER_DB_URL=sqlite+aiosqlite:///./job_schedule.db
JOB_SCHEDULER_SYNC_DB_URL=sqlite:///./job_schedule.db

# pick any string — used to sign JWT tokens
JWT_SECRET=change-this-to-something-random
EOF
```

You need API keys for at least one LLM provider. The system tries Ollama first (free, local), then falls back to Gemini, then OpenAI — so you only pay for calls when the cheaper options fail.

### 3. Start everything

```bash
docker compose up --build
```

First run takes a few minutes while Docker pulls images and installs Python packages. After that, rebuilds are fast because the dependency layer is cached.

You should see:
```
postgres   | database system is ready to accept connections
qdrant     | Qdrant HTTP listening on 6333
api        | Uvicorn running on http://0.0.0.0:8000
scheduler  | Scheduler process running — reconciling every 30s
```

### 4. Index your SOP documents (first run only)

Put your SOP PDF files in `data/raw/sop/`, then run:

```bash
docker compose exec api uv run python -c "
import sys; sys.path.insert(0, 'src')
from rag_pipeline.ingest import ingest_sop_docs
from rag_pipeline.chunking import chunk_text
from rag_pipeline.embed import embed_docs
embed_docs(chunk_text(ingest_sop_docs()))
print('done')
"
```

This chunks the PDFs, embeds them with OpenAI embeddings, and stores them in Qdrant. You only need to do this once unless your SOP documents change.

### 5. Try it

Generate a token (any JWT signed with your `JWT_SECRET`), then:

```bash
curl -X POST http://localhost:8000/v1/tickets/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_number": "INC-042",
    "session_id": "sess-001",
    "description": "High pick failure rate on SKU-008 in zone WH-A for the last 24 hours"
  }'
```

---

## Things worth knowing about the design

**The scheduler runs as a separate process, not inside the API**

Most tutorials shove a scheduler into the same process as the web server. That means if you run multiple API workers, each one starts its own scheduler and every job fires N times. Here the scheduler is its own container — it's the only process that owns APScheduler. API workers just write a row to the database when a user schedules a monitor, and the scheduler picks it up on its next reconcile cycle.

**The RAG pipeline uses hybrid search**

SOP retrieval combines dense vector search (semantic similarity) with BM25 sparse search (keyword matching), then fuses the results with Reciprocal Rank Fusion. Dense search handles meaning; BM25 handles exact WMS terms like `SKU-003` or `pick wave`. The results are better than either approach alone.

The retrieval also uses parent-document retrieval — small chunks (700 tokens) are what gets matched against the query, but the full SOP chapter section is what gets passed to the LLM. This means precise retrieval without losing the surrounding context that makes procedures make sense.

**SQL generation uses a skills catalogue**

Before generating SQL, the system injects the exact table schema, column semantics, and example queries for the relevant domain (inbound / outbound / inventory) into the prompt. The LLM doesn't have to guess column names — it gets told that `unit_qty` is the quantity field, that SKUs must be formatted as `SKU003` not `SKU-003`, and that you want aggregated results by default. This drastically reduces SQL errors.

**The SQL execution layer is read-only enforced**

Generated SQL is validated before running: only `SELECT`, `WITH`, and `EXPLAIN` are allowed, blocked keywords like `DELETE`, `DROP`, `INSERT` are rejected, and multiple statements are disallowed. This runs regardless of what the LLM generates.

**The application layer has no FastAPI imports**

The service layer (`diagnose_ticket_service`, `schedule_monitoring`) accepts plain Python parameters, not request objects. The same functions get called by HTTP handlers, scheduled jobs, and tests — nothing breaks if you swap the delivery mechanism.

---

## Tech stack

| Layer | What's used |
|---|---|
| API | FastAPI, Uvicorn, SlowAPI, JWT |
| Orchestration | LangGraph (StateGraph, Send, reducers) |
| LLM providers | OpenAI, Google Gemini, Groq, Ollama |
| RAG | Qdrant, OpenAI embeddings, FastEmbed BM25, RRF |
| Database | SQLAlchemy async, asyncpg, aiosqlite |
| Scheduling | APScheduler (dedicated process) |
| Streaming | SSE via asyncio pub/sub |
| Observability | LangSmith tracing, structured logging |
| CI | GitHub Actions (lint + tests on every push) |
| Containers | Docker + docker-compose |

---

## Development setup (without Docker)

If you'd rather run locally:

```bash
uv sync
PYTHONPATH=src uv run uvicorn api.app:app --reload --port 8000
```

You'll need Postgres and Qdrant running separately. For Qdrant:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

## Tests

```bash
PYTHONPATH=src uv run pytest src/tests/ --ignore=src/tests/evals -v
```

Tests cover the SQL safety guard — the layer that prevents LLM-generated SQL from mutating your database. No LLM calls, no network, runs in under a second.

`src/tests/evals/` has LangSmith evaluation suites that make real LLM calls — those are excluded from CI to avoid running up costs on every commit.

```bash
uvx ruff check src/
```
