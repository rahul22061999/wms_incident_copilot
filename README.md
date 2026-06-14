# WMS Incident Copilot API

> A multi-agent AI system that diagnoses Warehouse Management System incidents using LangGraph orchestration, hybrid RAG retrieval, parallel SQL execution, and scheduled monitoring — served over a production-structured FastAPI backend.

[![CI](https://github.com/rahuluk9632/wms-incident-api/actions/workflows/ci.yml/badge.svg)](https://github.com/rahuluk9632/wms-incident-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## What It Does

A WMS operator files an incident — a pick failure, inventory discrepancy, inbound delay. Instead of manually triaging across SQL databases and SOP binders, the operator sends the ticket to this API. The system:

1. **Classifies** the query and enriches it with WMS domain terminology via an LLM router
2. **Fans out** SQL lookups and SOP retrieval in parallel, or runs a multi-step ReAct agent for complex investigations
3. **Synthesises** all evidence into a structured diagnosis with root cause, confidence score, and citations
4. **Streams** live job updates back to the client over SSE
5. **Schedules** recurring monitoring runs that re-invoke the full graph on an interval

---

## Architecture

```
POST /v1/tickets/
        │
        ▼
   FastAPI + JWT Auth
        │
        ▼
 diagnose_ticket_service  (semaphore: max 10 concurrent runs)
        │
        ▼
┌─────────────────────────────────────────────────┐
│                  LangGraph StateGraph            │
│                                                  │
│  START ──► router_node  (classify + enrich)      │
│                │                                 │
│    ┌───────────┼──────────────┬──────────────┐   │
│    ▼           ▼              ▼              ▼   │
│  parallel   sequential    schedule      cancel   │
│  planner     agent         node          node    │
│    │           │                                 │
│  fan_out       │ (ReAct loop,                    │
│    │           │  4 tool calls max)              │
│  ┌─┴──────┐    │                                 │
│  ▼        ▼    │                                 │
│ SQL      SOP   │                                 │
│ node     node  │                                 │
│  └────────┴────┴─────────────────────────────┐   │
│                                              ▼   │
│                                    synthesizer   │
└─────────────────────────────────────────────────┘
        │
        ▼
  TicketDiagnosisResponse (structured JSON + citations)
```

The parallel barrier is implemented via LangGraph's `operator.add` reducer — `sql_node` and `sop_node` both emit partial state, LangGraph merges them automatically, and the synthesiser only advances once both branches are complete.

---

## Key Design Decisions

**Clean layer isolation**
The codebase follows a strict `api → application → domain → infrastructure → workflows` hierarchy. The application layer accepts plain parameters and has zero imports from FastAPI — the same service can be called by the HTTP handler, a scheduled job, or a test.

**Immutable runtime context**
`AppContext` is a `frozen=True, slots=True` dataclass built once at startup via `AppContextBuilder` and injected via `Depends`. No mutable singletons, no global state.

**Dedicated scheduler process**
The API workers never own an `AsyncIOScheduler`. A separate `scheduler_main.py` process is the only process allowed to register and fire APScheduler jobs. It reconciles active schedule rows from the database every 30 seconds — so API workers simply write a row to the DB and the scheduler picks it up, regardless of how many API replicas are running.

**Concurrency control**
A shared `asyncio.Semaphore` bounds concurrent LangGraph runs. Each graph run fans out to multiple LLM calls and SQL queries — without a ceiling, a burst of requests would saturate provider rate limits.

**LLM fallback chain**
Every node that calls an LLM uses a priority chain: `Ollama (local, zero cost) → Google Gemini → OpenAI`. If Ollama is unavailable the chain falls through silently.

**Per-node LLM response caching**
Each node has its own isolated cache backend. The same input to the same model always hits. Clearing one node's cache during debugging does not affect others.

---

## Hybrid RAG Pipeline

SOPs are indexed using a **two-level parent-document retrieval** strategy combined with **hybrid search** (dense + sparse + RRF):

```
Offline (index time)
────────────────────
PDF → chapter-level parent documents (regex split on headings)
    → 700-token child chunks with 100-token overlap
    → child chunks embedded with OpenAI text-embedding-3-small
    → stored in Qdrant with both dense (cosine) and sparse (BM25) vectors

Online (query time)
────────────────────
User query
  ├── Dense search   (semantic similarity via OpenAI embedding)
  └── Sparse search  (BM25 keyword match via FastEmbed Qdrant/bm25)
          │
     Reciprocal Rank Fusion (RRF) — Qdrant native
          │
     child chunk matched → parent chapter fetched from pickle store
          │
     full chapter section passed to LLM (not the small chunk)
```

Dense retrieval captures semantic meaning; BM25 captures exact WMS terminology (`SKU-003`, `ASN`, `pick wave`). RRF fuses both ranked lists without tuning weights.

---

## Context Engineering

The system applies several deliberate techniques to manage what the LLM sees at each step:

| Technique | Where | Effect |
|---|---|---|
| **Query enrichment** | `router_node` | Raw user query rewritten with WMS terminology before any downstream call |
| **Structured output** | All nodes | Pydantic schemas enforced via `method="json_schema"` — eliminates hallucinated keys |
| **Skill-injected SQL context** | `sql_generate_query_node` | Table schema, column semantics, and example queries injected per domain before SQL generation |
| **Token-triggered summarisation** | `sequential_agent` | Conversation history compressed at 10k tokens so the agent never hits context limits |
| **Tool-call clearing** | `sequential_agent` | Old tool results replaced with `[cleared]` when context grows — keeps recent evidence, drops stale output |
| **Parent-document retrieval** | `sop_retrieval_tool` | Small chunks retrieved for precision; full chapter sections returned for rich context |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI, Uvicorn, SlowAPI (rate limiting), JWT auth |
| **Orchestration** | LangGraph (StateGraph, Send, conditional edges, reducers) |
| **LLM Providers** | OpenAI GPT, Google Gemini, Groq Llama, Ollama (local) |
| **RAG** | Qdrant, OpenAI `text-embedding-3-small`, FastEmbed BM25, LangChain text splitters |
| **Database** | SQLAlchemy async, asyncpg (Postgres), aiosqlite |
| **Scheduling** | APScheduler (dedicated process, SQLAlchemy job store) |
| **Streaming** | Server-Sent Events via asyncio pub/sub `JobEventBus` |
| **Observability** | LangSmith tracing, structlog, RotatingFileHandler |
| **Packaging** | uv, pyproject.toml |
| **Linting** | Ruff |
| **CI** | GitHub Actions |
| **Containers** | Docker, docker-compose (API + scheduler + Postgres + Qdrant) |

---

## Project Structure

```
src/
├── api/                    # HTTP delivery layer only
│   └── v1/
│       ├── auth.py         # JWT bearer validation
│       ├── routes/         # tickets, monitoring (SSE)
│       └── schemas/        # request / response models
│
├── application/            # Use-case layer — no HTTP imports
│   ├── diagnose_ticket.py  # runs the LangGraph graph
│   ├── schedule_monitoring.py
│   └── stream_job_updates.py
│
├── domain/                 # Pure Python — no I/O, no frameworks
│   ├── states/             # LangGraph state dataclasses
│   └── schemas/
│
├── infrastructure/         # External wiring
│   ├── app_context.py      # frozen runtime context dataclass
│   ├── app_context_builder.py
│   ├── databases.py        # SQLAlchemy engines + sessions
│   ├── llm_clients.py      # LLM factory (lru_cache, multi-provider)
│   ├── operation_cache.py  # per-node LLM response caches
│   ├── job_event_bus.py    # asyncio pub/sub for SSE
│   └── repositories/
│
├── workflows/              # LangGraph graph definitions
│   ├── graph/              # compiled StateGraphs
│   ├── nodes/              # individual agent nodes
│   ├── edges/              # conditional routing functions
│   ├── prompts/            # system prompts per node
│   └── tools/              # SQL + RAG tools
│
├── rag_pipeline/           # offline: ingest → chunk → embed
├── workers/                # scheduled job runner
├── utils/                  # logging config, SQL safety guard
├── config.py               # pydantic-settings
└── scheduler_main.py       # dedicated scheduler process entry point
```

---

## Getting Started

### Prerequisites

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- Docker (for Postgres + Qdrant)

### 1. Clone and install

```bash
git clone https://github.com/rahuluk9632/wms-incident-api.git
cd wms-incident-api
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# fill in API keys and database URLs
```

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | GPT + embeddings |
| `GOOGLE_API_KEY` | Gemini fallback |
| `GROQ_API_KEY` | Llama fallback |
| `DATABASE_URL` | Async Postgres (WMS database) |
| `JWT_SECRET` | Token signing secret |
| `LANGSMITH_API_KEY` | Tracing (optional) |

### 3. Start the full stack

```bash
docker compose up --build
```

This starts the API, dedicated scheduler process, Postgres, and Qdrant in one command.

### 4. Index SOPs (first run only)

```bash
PYTHONPATH=src uv run python -c "
from rag_pipeline.ingest import ingest_sop_docs
from rag_pipeline.chunking import chunk_text
from rag_pipeline.embed import embed_docs
embed_docs(chunk_text(ingest_sop_docs()))
"
```

### 5. Diagnose a ticket

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

## Running Tests

```bash
# unit tests (no LLM calls, no external dependencies)
PYTHONPATH=src uv run pytest src/tests/ --ignore=src/tests/evals -v

# lint
uvx ruff check src/
```

`src/tests/evals/` contains LangSmith evaluation suites that call real LLM endpoints — excluded from CI to avoid cost on every push.

---

## CI Pipeline

Every push and pull request to `main` runs:

```
Checkout → Python 3.12 → uv sync → ruff lint → app import check → pytest
```
