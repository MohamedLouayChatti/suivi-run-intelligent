# AI Support Intelligence Platform

## Purpose

This project is an enterprise-grade modular monolith built during an internship.

The objective is **not** to build another chatbot.

The objective is to reduce unnecessary Level 3 escalations by helping Level 2 support engineers reuse organizational knowledge.

The platform combines:

- Incident management
- Knowledge retrieval
- AI-assisted troubleshooting
- Knowledge generation
- Retrieval-Augmented Generation (RAG)

---

# Architectural Goals

Design decisions should favor:

- loose coupling
- modularity
- maintainability
- replaceable infrastructure
- explicit boundaries
- domain-driven design
- asynchronous processing
- scalability

Implementation convenience should never compromise architecture.

---

# Architecture

The application is an Async FastAPI Modular Monolith based on Clean Architecture within each module.

Core technologies:

- Python
- FastAPI
- SQLAlchemy Async
- Alembic
- PostgreSQL
- pgvector
- Redis
- LangGraph
- JWT Authentication with external auth provider (Clerk)
- Server-Sent Events
- uv

Communication between modules occurs through:

- Application interfaces (synchronous)
- Domain Events (asynchronous)

Never access another module's database models directly.

---

# Shared Infrastructure Foundation

The shared configuration and database packages provide the application-wide persistence baseline used by every module.

## Shared Configuration

The shared configuration package lives in `app/shared/config/`.

`app/shared/config/settings.py` owns the `Settings` model.

`Settings`:

- loads configuration from the project's `.env` file
- exposes typed environment-driven settings
- is the only source of the PostgreSQL connection string
- must be used by shared infrastructure instead of hardcoded connection values

## Shared Database

The shared database package lives in `app/shared/database/`.

`app/shared/database/base.py` defines the application's single shared `DeclarativeBase`.

`Base`:

- is the parent class for every ORM model in every module
- owns shared SQLAlchemy metadata for the whole application
- contains no engine logic, session logic, helper methods, or business rules

`app/shared/database/engine.py` creates the application's single `AsyncEngine`.

`AsyncEngine`:

- is owned globally by the application
- reads the PostgreSQL URL from `Settings`
- uses SQLAlchemy 2.x async configuration
- applies engine-level options only
- does not create sessions, manage transactions, or implement repository behavior

`app/shared/database/session.py` defines the shared async session factory.

`async_sessionmaker`:

- is bound to the shared `AsyncEngine`
- creates `AsyncSession` instances for application use
- configures safe defaults such as `expire_on_commit=False` and `autoflush=False`
- does not commit, rollback, publish events, or implement Unit of Work behavior

## Alembic

Alembic is configured for async migrations in `alembic/env.py`.

The migration environment:

- imports the shared `DeclarativeBase`
- sets `target_metadata` to `Base.metadata`
- reads the database URL from `Settings`
- imports ORM model modules so autogenerate can discover future models
- runs online migrations through SQLAlchemy async execution
- relies on SQLAlchemy metadata autogeneration instead of manual SQL

## Migration Workflow

Schema evolution follows this flow:

1. Add or update ORM models under module infrastructure persistence packages.
2. Ensure new ORM classes inherit from the shared `Base`.
3. Run `alembic revision --autogenerate -m "..."`.
4. Review the generated revision.
5. Apply it with `alembic upgrade head`.

## Project Structure

This task added the following shared persistence foundation files:

- `app/shared/config/settings.py`
- `app/shared/database/base.py`
- `app/shared/database/engine.py`
- `app/shared/database/session.py`
- `alembic/env.py`

---

# Layers

Every module follows:

API

↓

Application

↓

Domain

↓

Infrastructure

Dependencies point inward only.

Infrastructure depends on Domain.

Domain never depends on Infrastructure.

---

# Module Responsibilities

## Auth

Authentication

Authorization

User identity

RBAC

---

## Ticket Management

Owns the ticket lifecycle and domain invariants.

The Ticket Management application layer follows CQRS.

Commands are immutable DTOs, one handler per command.

Queries are read models, one handler per query.

Application handlers orchestrate the write side through an async Unit of Work, use a dedicated EventPublisher port, and publish events only after a successful commit.

Read handlers use a dedicated TicketReadRepository and return DTO read models.

The current domain event model exposes:

- TicketCreated
- TicketAssigned
- TicketStatusChanged
- PriorityChanged
- CommentAdded
- CommentEdited
- CommentDeleted
- AttachmentAdded
- AttachmentDeleted
- TicketArchived
- TicketRestored
- TicketReassigned
- TicketTransferred

Archive, restore, reassign, transfer, comment edit/delete, and attachment delete flows now publish dedicated domain events after commit.

Domain model currently includes:

- Ticket aggregate
- Comment entity
- Attachment entity
- Application, Priority, and Status enums
- TicketRepository contract

Business rules currently covered in the domain layer:

- Ticket creation and validation
- Assignment and reassignment
- Status transitions between OPEN, IN_PROGRESS, PENDING, RESOLVED, and CLOSED
- Priority changes
- Application transfers
- Comment creation, editing, deletion, and comment attachments
- Ticket attachment creation and deletion
- Archive handling
- Guard clauses for empty titles, descriptions, comments, and invalid transitions

Publishes domain events for:

- TicketCreated
- TicketAssigned
- TicketStatusChanged
- PriorityChanged
- CommentAdded
- CommentEdited
- CommentDeleted
- AttachmentAdded
- AttachmentDeleted
- TicketArchived
- TicketRestored
- TicketReassigned
- TicketTransferred

Must never know AI exists.

---

## Knowledge Base

Responsible for:

Document ingestion

Chunking

Embedding generation

Hybrid retrieval

Vector indexing

---

## Incident Intelligence

Listens to TicketCreated.

Finds similar historical incidents.

Combines:

- semantic similarity
- metadata filtering
- ranking

Produces recommendations.

---

## Conversational Assistant

Owns LangGraph.

Provides AI assistance.

Never directly queries databases.

Uses module interfaces only.

Streams responses through SSE.

Agent execution is asynchronous and decoupled from HTTP requests.

The agent run is a background job.

---

## Knowledge Generation

Listens to TicketClosed.

Creates draft knowledge articles.

Requires human approval.

Never auto-publishes.

---

## Analytics

Provides reporting.

Should remain independent from operational workflows.

---

# AI Principles

LLMs are infrastructure.

Never call OpenAI (or another provider) directly from business logic.

Use abstractions:

- LLMProvider
- EmbeddingProvider
- Reranker

Infrastructure provides implementations.

---

# Event-Driven Architecture

Modules communicate using domain events.

Examples:

TicketCreated

TicketAssigned

TicketStatusChanged

PriorityChanged

CommentAdded

AttachmentAdded

↓

Incident Intelligence

↓

Knowledge Generation

↓

Analytics

Avoid direct module coupling whenever asynchronous reactions are appropriate.

---

# Async Principles

All I/O must be asynchronous.

Use:

- async SQLAlchemy
- async Redis
- async LangGraph
- async HTTP clients

CPU-intensive work should execute in background workers.

---

# Repository Rules

Repositories belong to the Domain.

Implementations belong to Infrastructure.

Application depends only on repository interfaces.

---

# Public Module APIs

Each module exposes only its Application layer.

Other modules may never import:

- ORM models
- Infrastructure
- Database tables
- Internal services

---

# Architectural Priorities

When making decisions, prioritize in this order:

1. Correct architecture
2. Clear module boundaries
3. Domain modeling
4. Maintainability
5. Performance
6. Implementation simplicity
7. Clean architecture principles

---

# Updating this document

Whenever architecture changes:

- Update this document.
- Keep module responsibilities current.
- Record new domain events.
- Document new interfaces.
- Explain major architectural decisions.
- Keep folder structure synchronized with reality.

This file is the single source of truth for the project's architecture.