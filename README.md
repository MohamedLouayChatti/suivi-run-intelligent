<div align="center">

# Suivi RUN Intelligent

**AI-powered support intelligence platform** — ticket management, incident similarity retrieval, and a data-grounded conversational agent, built as a single modular monolith.

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)](app/main.py)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)](frontend)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-4169E1?logo=postgresql&logoColor=white)](app/shared/database)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector%20search-DC244C)](app/modules/knowledge_base)
[![LangGraph](https://img.shields.io/badge/LangGraph-agent-1C3C3C)](app/modules/conversational_assistant)

</div>

---

Support teams accumulate incident history that never gets reused — the same problem gets re-diagnosed from scratch because nobody remembers (or can find) the ticket that already solved it. Suivi Run Intelligent closes that loop: every new ticket is automatically embedded and matched against historical incidents, and a permission-aware conversational agent lets engineers query the organization's ticket data, activity, and analytics in natural language instead of hand-building filters.

It is not a chatbot wrapped around a ticketing system — it's a ticketing system whose domain model the AI features are built *on top of*, with the same authorization rules enforced in both places.

## Highlights

- **Modular monolith, not a ball of mud.** Seven backend modules, each with an enforced Clean Architecture layering (`api` → `application` → `domain` → `infrastructure`), communicating only through application-layer interfaces, domain events, or background jobs — never through shared database tables or imported ORM models.
- **Calibrated retrieval, not a default threshold.** The embedding model was selected by benchmarking three candidates against the real historical corpus, and the similarity cutoff was solved by bisection against that same corpus rather than picked by hand.
- **A tool-using agent with real guardrails.** 18 tools, two independent authorization layers (tool availability + per-call resource checks), a bounded iteration budget with graceful degradation instead of hard failure, and output validation that makes hallucinated ticket links structurally impossible.
- **CQRS with an audit trail for free.** Every write is a command handled by exactly one handler, followed by a domain event published only after a successful commit — which is also what feeds a 36-event-type, append-only audit log and a 25-event-type notification system, without either being hardcoded into the write path.
- **Three permission layers, one source of truth.** Role-based, per-instance, and collection-scope authorization all resolve against the same 41-permission dependency graph — enforced identically on HTTP routes and on agent tool calls.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (async), Python 3.13, SQLAlchemy 2.x, Alembic |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, TanStack Query, Tailwind CSS |
| Database | PostgreSQL (async via `asyncpg`) |
| Vector search | Qdrant Cloud |
| LLM / embeddings | Ollama — `bge-m3` (embeddings), `gemma4` (chat), `gpt-oss:20b` (titling) |
| Agent orchestration | LangGraph (`StateGraph` only — no chat-model/tool-wrapper abstractions) |
| Auth | Clerk (JWT sessions + signed webhooks) |
| Scheduling | APScheduler |
| Realtime delivery | Server-Sent Events (notifications, agent streaming) |

## Architecture

A single FastAPI process hosts seven independently-layered modules against one Postgres database:

```
┌─────────────────────────────────────────────────────────────────────┐
│                              FastAPI process                         │
│                                                                        │
│   auth   ticket_management   knowledge_base   analytics   audit      │
│                    notifications   conversational_assistant          │
│                                                                        │
│   each module:  api/ → application/ → domain/ → infrastructure/      │
└──────────┬───────────────────────┬──────────────────────┬────────────┘
           │                       │                      │
      PostgreSQL                Qdrant                 Ollama
   (system of record)      (vector corpus)        (embeddings + chat)
```

Every module follows the same four-layer split, and the dependency direction is enforced, not aspirational — `domain/` never imports SQLAlchemy, FastAPI, or Qdrant types:

```
app/modules/<module>/
├── api/              HTTP routes, request/response schemas
├── application/      commands, queries, DTOs, orchestration
├── domain/           entities, value objects, business rules — framework-free
└── infrastructure/   ORM models, repositories, external providers, background jobs
```

| Module | Owns |
|---|---|
| `auth` | Identity, roles, permissions, application/team staffing |
| `ticket_management` | Ticket lifecycle, comments, attachments, history, bulk import |
| `knowledge_base` | Embedding pipeline, vector corpus, similarity graph |
| `analytics` | KPIs, activity trends, application health scoring |
| `audit` | Append-only log of every domain event |
| `notifications` | In-app notifications and SSE delivery |
| `conversational_assistant` | LangGraph agent, tool catalogue, conversation titling |

**Cross-module communication** happens through exactly three channels — application-layer interfaces for synchronous reads, an in-process domain event bus for reactions, and a background job queue for anything too slow to run inline. Modules never import each other's ORM models or infrastructure code (one sanctioned exception: Analytics reads Ticket Management's tables directly for reporting, documented as a one-off).

**CQRS** separates every write from every read: 44 command handlers each own a single aggregate mutation and publish a domain event after commit; 38 query handlers run directly against dedicated read models and return DTOs, bypassing the domain layer entirely. This is what lets the audit log, notifications, and background indexing all react to the same write without the write path knowing they exist.

**Authorization** is three composable layers checked on every request and every agent tool call:

1. **RBAC** — a permission check against a resolved, cached set (role permissions ∪ direct grants − revocations, closed under a dependency graph).
2. **Instance policy** — "can *this* caller act on *this specific* resource" (assignee-only ticket transitions, author-only comment edits, etc.).
3. **Collection scope** — list/search endpoints silently narrow to what the caller is staffed on rather than 403ing, unless they hold the relevant breadth permission.

## AI systems

### Incident similarity

New tickets are embedded and matched against historical incidents automatically, in the background:

```
ticket created → preprocess description → embed (bge-m3, 1024-d)
              → write to Qdrant → rank candidates → persist top-7 matches
              → refresh the one-hop neighbors this ticket now links to
```

- **Deterministic preprocessing** normalizes nine families of domain-specific identifiers (incident refs, order refs, site codes, ...) into typed placeholders before embedding — applied identically at index time and query time, so retrieval quality is never sensitive to phrasing drift.
- **Empirically selected model.** `bge-m3` was benchmarked against two alternatives on the real historical ticket corpus using the production ranking code, not a generic leaderboard.
- **A calibrated similarity threshold** (`0.6411`), solved by bisection against that same corpus rather than set by hand.
- **Exact identifier matches always outrank semantic similarity** — a ticket referencing the same incident number is relevant regardless of cosine distance.
- **Tenant-partitioned vector search**: the application filter is a hard partition key in the Qdrant query itself, not a post-filter — cross-application leakage is structurally impossible, not just checked for.

### Conversational agent

A LangGraph state machine (`agent → tools → agent`) with 18 tools spanning tickets, engineers, and analytics — each backed by the platform's own application-layer handlers, so the agent can never see or do more than a human user with the same permissions could.

- **Two-layer tool authorization**: tools the caller lacks permission for are never bound into the graph, and every tool re-checks resource-level access at call time.
- **Bounded and graceful**: a 12-iteration cap doesn't fail the run — the final turn drops all tools and forces an answer with whatever was gathered, rather than discarding a paid-for partial result.
- **Grounded citations**: the agent links to tickets using an internal reference scheme (`ticket:<uuid>`) that is validated against the tool calls actually made in that run before the message is ever stored — an invented or unauthorized ticket reference cannot survive to the response.
- **Schema-strict tool calls**: every tool argument is validated against a Pydantic schema with `extra="forbid"`, and rejections return the legal values inline so the model can self-correct instead of burning its iteration budget guessing.

### Conversation titling

An independent single-shot background job (separate model, separate failure policy from the chat agent) generates a short title from the first message, with a code-level normalizer — not just prompt instructions — enforcing length, format, and stripping any leaked model artifacts.

## Getting started

**Prerequisites:** Python 3.13+, `uv`, PostgreSQL, and reachable Clerk / Qdrant / Ollama credentials (only `DATABASE_URL` is required to boot — everything else fails loudly, by name, the first time it's actually needed).

```bash
# Backend
uv sync
uv run alembic upgrade head

# Seed reference data (roles, permissions — required before first use)
uv run python -m app.scripts.seeding.roles_permissions.seed

# Run
uv run uvicorn app.main:app --reload
```

```bash
# Frontend
cd frontend
npm install
npm run dev
```

Configuration is environment-variable driven (`app/shared/config/settings.py`). Model names (`bge-m3`, `gemma4:cloud`, `gpt-oss:20b-cloud`) are intentionally pinned in code rather than configurable — swapping a model is a reviewed code change, not a silent runtime flip.

## Project structure

```
app/
├── main.py                     FastAPI entry point
├── lifespan.py                 startup/shutdown composition root
├── shared/                     cross-cutting ports: config, database, security, storage
├── workers/                    background job queue + scheduler
├── modules/                    the seven modules described above
└── scripts/seeding/            role/permission/user/ticket seeders

frontend/
└── src/
    ├── app/                    Next.js routes
    ├── features/                per-domain UI, mirrors backend modules
    ├── services/                API client, SSE client
    └── lib/                     permission mirrors, cache invalidation rules

alembic/                       database migrations
notebooks/                     embedding model evaluation, threshold calibration
```

## Design notes

A few decisions that shaped the codebase and are worth knowing before touching it:

- **Writes commit, then publish.** Domain events fire only after a successful commit, never before — so a failed transaction can never leave a stray notification or audit entry behind.
- **Background work is losable by design.** There is no message broker; only recomputable work (re-embedding a ticket, refreshing a health baseline) is scheduled this way. Nothing that needs a delivery guarantee goes through it.
- **Bulk imports are all-or-nothing.** Every row in a batch ticket import is validated before any of them are written, and every error is collected — not just the first one — so an operator fixes a file once instead of once per failed attempt.
- **Cross-store consistency is compensating, not transactional.** A ticket batch import that fails partway through embedding unwinds by deleting the partial vector writes before the partial ticket writes, in that order, every time.
- **Language is decided by audience, not by layer.** Everything a developer reads (code, logs, exception names) is English; everything a support engineer or end user reads (notifications, import error reports, agent responses) is French — enforced at the point where the string is written, not translated downstream.

## Current limitations

- No automated test suite (test tooling is configured but unused).
- No CI/CD pipeline or containerization.
- Single-process design — the event bus, job scheduler, and SSE connections all assume one running instance.
- No rate limiting on any endpoint, including the conversational agent.

---

<div align="center">

Built solo as an internship project

</div>
