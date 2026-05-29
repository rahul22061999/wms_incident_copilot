# WMS Incident Copilot API

> A production-grade multi-agent AI system that diagnoses Warehouse Management System (WMS) incidents using LangGraph orchestration, parallel tool execution, RAG-powered SOP lookup, and scheduled monitoring jobs — all served over a FastAPI backend with JWT auth and real-time SSE streaming.

[![CI](https://github.com/rahuluk9632/wms-incident-api/actions/workflows/ci.yml/badge.svg)](https://github.com/rahuluk9632/wms-incident-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## What It Does

A WMS operator files an incident ticket — a pick failure, inventory discrepancy, inbound delay. Instead of manually triaging across SQL databases and SOP binders, the operator sends the ticket to this API. The system:

1. **Routes** the query with an LLM classifier: parallel investigation, sequential deep-dive, or schedule a recurring monitor
2. **Fans out** SQL lookups and RAG-based SOP retrieval in parallel
3. **Synthesizes** all evidence into a structured diagnosis with root cause, confidence, and recommended actions
4. **Streams** live job updates back to the client over SSE
5. **Schedules** recurring monitoring runs that re-invoke the diagnosis graph on an interval

---

## Architecture

```
POST /v1/tickets/
        │
        ▼
   FastAPI + JWT
        │
        ▼
 diagnose_ticket_service          ← application layer
        │  (semaphore: max 10 concurrent graph runs)
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                      LangGraph StateGraph                        │
  │                                                                  │
  │   START ──► router_node  (classifies intent + enriches query)   │
  │                 │                                                │
  │    ┌────────────┼───────────────┬────────────────┐              │
  │    ▼            ▼               ▼                ▼              │
  │  parallel     sequential     scheduler      cancel_schedule      │
  │  planner       agent           node             node             │
  │    │             │               │                │              │
  │  fan_out         │               │                │              │
  │    │             │               │                │              │
  │  ┌─┴──────┐      │               │                │              │
  │  ▼        ▼      │               │                │              │
  │ SQL      SOP     │               │                │              │
  │ node     node    │               │                │              │
  │  └────────┴──────┴───────────────┴────────────────┘              │
  │                          │                                       │
  │                          ▼                                       │
  │                   synthesizer_node ──► END                       │
  └─────────────────────────────────────────────────────────────────┘
        │
        ▼
  TicketDiagnosisResponse (structured JSON)
```

### Node Responsibilities

| Node | Role |
|---|---|
| `router_node` | LLM classifier — detects intent and enriches the query with WMS domain terminology. Fallback chain: Ollama → Gemini → OpenAI |
| `plan_parallel_subtask_node` | Decomposes the enriched query into parallel subtasks (SQL + SOP) |
| `sql_lookup_node` | Fans out to the SQL subgraph — generates, validates, and executes safe SQL against the WMS database |
| `sop_retrieval_node` | RAG lookup — retrieves relevant SOP chunks from the Qdrant vector store |
| `sequential_agent` | Tool-calling ReAct agent for multi-step investigations; includes retry, fallback, call-limit, and summarization middleware |
| `synthesizer_node` | Merges all parallel results into a structured diagnosis |
| `schedule_registrar_node` | Registers an APScheduler interval job that re-runs the graph on a schedule |
| `cancel_schedule_node` | Cancels a scheduled job by ID |

### SQL Subgraph

```
START → sql_load_skills_node → sql_generate_query_node → sql_run_sql_node → END
```

Generates schema-aware SQL using a skills catalogue, validates the query, and executes it against the WMS Postgres database.

---

## Key Design Decisions

**Parallel barrier via LangGraph reducers** — `parallel_results` is typed `Annotated[List, operator.add]`. When `sql_lookup_node` and `sop_retrieval_node` both emit partial state, LangGraph merges them automatically. The synthesizer node only advances after both branches are complete.

**Layer isolation** — The application layer (`diagnose_ticket_service`) never imports from the API layer. It accepts plain parameters, not request objects. The same service can be called by the HTTP handler, a scheduled job, or a test without touching FastAPI.

**Immutable app context** — `AppContext` is a `frozen=True, slots=True` dataclass built once at startup and injected via `Depends`. No global state. No mutable singletons.

**Idempotent job scheduling** — Job IDs are SHA-256 hashes of `(query, interval, ticket, user)`. Scheduling the same monitor twice replaces the existing job rather than creating a duplicate.

**LLM fallback chain** — Every classification call has a provider priority: local Ollama first (zero cost, lowest latency), then Google Gemini, then OpenAI. If Ollama is unavailable, the chain falls through silently.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI, Uvicorn, SlowAPI (rate limiting), JWT auth |
| **Orchestration** | LangGraph (StateGraph, Send, conditional edges) |
| **LLM Providers** | OpenAI GPT-5-nano, Google Gemini 2.5 Flash Lite, Groq Llama 3.1, Ollama (local) |
| **RAG** | Qdrant vector store, OpenAI `text-embedding-3-small`, LangChain text splitters |
| **Database** | SQLAlchemy async, asyncpg (Postgres), aiosqlite |
| **Scheduling** | APScheduler (AsyncIOScheduler + SQLAlchemyJobStore) |
| **Streaming** | Server-Sent Events via asyncio pub/sub `JobEventBus` |
| **Observability** | LangSmith tracing, structlog, RotatingFileHandler |
| **Config** | pydantic-settings, `.env` |
| **Packaging** | uv, pyproject.toml |
| **Linting** | Ruff (E, F, I rules) |
| **CI** | GitHub Actions |

---

## Project Structure

```
src/
├── api/                        # Delivery layer (HTTP only)
│   └── v1/
│       ├── auth.py             # JWT bearer token validation
│       ├── routes/
│       │   ├── tickets.py      # POST /v1/tickets/
│       │   └── monitoring.py   # GET  /v1/tickets/{id}/jobs/stream
│       └── schemas/            # Request / response / error models
│
├── application/                # Use-case layer (no HTTP imports)
│   ├── diagnose_ticket.py      # Runs the LangGraph diagnosis
│   ├── schedule_monitoring.py  # Creates / cancels APScheduler jobs
│   └── stream_job_updates.py   # SSE event generator
│
├── domain/                     # Pure Python — no I/O, no frameworks
│   ├── states/                 # LangGraph state dataclasses
│   └── schemas/                # Pydantic read models
│
├── infrastructure/             # External wiring
│   ├── app_context.py          # Frozen runtime context dataclass
│   ├── app_context_builder.py  # Builds AppContext at startup
│   ├── databases.py            # SQLAlchemy engines + session factories
│   ├── llm_clients.py          # LLM factory functions (lru_cache, multi-provider)
│   ├── operation_cache.py      # LangChain LLM response caches
│   ├── job_event_bus.py        # asyncio pub/sub for SSE
│   ├── orm/                    # SQLAlchemy ORM models
│   └── repositories/           # Data access (queries only, no business logic)
│
├── workers/                    # Background job execution
│   ├── monitoring_job_runner.py
│   └── monitoring_job_entrypoint.py
│
├── workflows/                  # LangGraph graph definitions
│   ├── graph/                  # Compiled StateGraphs
│   ├── nodes/                  # Individual agent nodes
│   ├── edges/                  # Conditional routing functions
│   ├── prompts/                # System prompts per node
│   └── tools/                  # LangChain tools (SQL, RAG)
│
├── rag_pipeline/               # Offline: chunk → embed → store
├── utils/                      # Logging config, SQL helpers
└── config.py                   # pydantic-settings (all env vars)
```

---

## Getting Started

### Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) — `brew install uv`
- A running PostgreSQL instance (WMS database)
- Qdrant for RAG — `docker run -p 6333:6333 qdrant/qdrant`
- Ollama for local LLM (optional) — `brew install ollama && ollama pull llama3.1`

### 1. Clone and install

```bash
git clone https://github.com/rahuluk9632/wms-incident-api.git
cd wms-incident-api
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# edit .env with your credentials
```

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key |
| `OPENAI_API_KEY` | Yes | OpenAI API key (GPT + embeddings) |
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `GROQ_API_KEY` | Yes | Groq API key (Llama 3.1) |
| `OLLAMA_API_KEY` | Yes | Any string if running locally |
| `DATABASE_URL` | Yes | Async WMS Postgres URL |
| `MEMORIES_DB_URL` | Yes | Async SQLite/Postgres for memory store |
| `LANGSMITH_API_KEY` | Yes | LangSmith tracing key |
| `JWT_SECRET` | Yes | Secret for signing JWT tokens |
| `MAX_GRAPH_SEMAPHORE` | No | Max concurrent graph runs (default: `10`) |
| `RATE_LIMIT_DEFAULT` | No | API rate limit (default: `5/minute`) |

### 3. Run the API

```bash
PYTHONPATH=src uv run uvicorn api.app:app --reload --port 8000
```

### 4. Index SOPs (first time only)

```bash
PYTHONPATH=src uv run python -m rag_pipeline.ingest
PYTHONPATH=src uv run python -m rag_pipeline.embed
```

---

## API Reference

### Diagnose a ticket

```http
POST /v1/tickets/
Authorization: Bearer <token>
Content-Type: application/json

{
  "ticket_number": "INC0042",
  "session_id": "sess_abc123",
  "description": "High pick failure rate on SKU-008 in zone WH-A for the last 24 hours"
}
```

**Response**

```json
{
  "ticket_number": "INC0042",
  "session_id": "sess_abc123",
  "user_id": "rahul",
  "result": {
    "summarized_issue": "SKU-008 had 42 pick failures in WH-A-A13-BIN7 over 24h. Location is flagged as blocked.",
    "root_cause": "Blocked bin location not cleared after last cycle count",
    "confidence": "high",
    "recommended_actions": [
      "Clear the blocked flag on WH-A-A13-BIN7 via WMS admin",
      "Investigate whether cycle count completed successfully",
      "Re-allocate open picks for SKU-008 to an alternate location"
    ],
    "source_type": "sql"
  }
}
```

### Stream live job updates (SSE)

```http
GET /v1/tickets/INC0042/jobs/stream
Authorization: Bearer <token>
Accept: text/event-stream
```

```
data: monitor_schedule_created

data: {"job_id": "abc123", "status": "running", "tick": 1}

data: {"job_id": "abc123", "status": "complete", "result": "..."}
```

---

## Running Tests

```bash
# Unit tests (no LLM calls, no external dependencies)
PYTHONPATH=src uv run pytest tests/ --ignore=tests/evals -v

# Lint
uvx ruff check src/
```

`tests/evals/` contains LangSmith evaluation suites that call real LLM endpoints. Run those separately with valid API keys — they are excluded from CI to avoid costs on every commit.

---

## CI Pipeline

Every push and pull request to `main` automatically runs on GitHub Actions:

```
Checkout → Python 3.12 setup → uv sync → ruff lint → app boot check → pytest (unit only)
```

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the full configuration.

---

## Roadmap

- [ ] WebSocket support alongside SSE
- [ ] LangGraph Postgres checkpoint for persistent graph state across restarts
- [ ] OpenTelemetry trace export
- [ ] Multi-tenant session isolation
- [ ] Admin dashboard for scheduled job monitoring

---

## License

MIT
