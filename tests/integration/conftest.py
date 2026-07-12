"""
Shared fixtures for all integration tests.

Isolation strategy
------------------
Every test that touches the database receives a fresh ``AsyncSession`` via
the ``db_session`` fixture.  After each test, the session is rolled back so
no data leaks between tests.

The ``uow`` fixture injects that same test session into
``SqlAlchemyUnitOfWork`` so the unit-of-work's writes are covered by the
same rollback boundary.

The ``test_unit_of_work.py`` suite is the sole exception: it must verify
cross-session commit visibility and therefore manages its own independent
sessions and explicit cleanup.  See that module for details.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import (
    InMemoryEventPublisher,
)
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
    SqlAlchemyTicketReadRepository,
)
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.shared.database.engine import engine
from app.shared.database.session import async_session_factory
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def db_engine():
    """Return the shared application engine (session-scoped – one pool for all tests)."""
    return engine


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """
    Yield a fresh ``AsyncSession`` for one test, then roll back.

    Uses ``async_session_factory`` so we work with the real session
    configuration (expire_on_commit=False, autoflush=False).
    """
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Repository fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ticket_repository(db_session: AsyncSession) -> SqlAlchemyTicketRepository:
    """Write-side repository wired to the test session."""
    return SqlAlchemyTicketRepository(db_session)


@pytest.fixture
def ticket_read_repository(db_session: AsyncSession) -> SqlAlchemyTicketReadRepository:
    """Read-side repository wired to the test session."""
    return SqlAlchemyTicketReadRepository(db_session)


# ---------------------------------------------------------------------------
# Unit of Work fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def uow(db_session: AsyncSession) -> SqlAlchemyUnitOfWork:
    """
    ``SqlAlchemyUnitOfWork`` wired to the test session.

    The UoW will commit/rollback against this session, but the outer
    ``db_session`` fixture rolls everything back afterwards.
    """
    return SqlAlchemyUnitOfWork(session=db_session)


# ---------------------------------------------------------------------------
# Event infrastructure fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def subscription_registry() -> SubscriptionRegistry:
    """Fresh ``SubscriptionRegistry`` per test."""
    return SubscriptionRegistry()


@pytest.fixture
def event_bus(subscription_registry: SubscriptionRegistry) -> InMemoryEventBus:
    """``InMemoryEventBus`` wired to the test registry."""
    return InMemoryEventBus(subscription_registry)


@pytest.fixture
def event_publisher(event_bus: InMemoryEventBus) -> InMemoryEventPublisher:
    """``InMemoryEventPublisher`` wired to the test event bus."""
    return InMemoryEventPublisher(event_bus)
