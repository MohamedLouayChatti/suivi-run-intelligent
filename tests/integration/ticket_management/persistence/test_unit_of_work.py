"""
Integration tests for ``SqlAlchemyUnitOfWork``.

Isolation strategy for this module
------------------------------------
The UoW tests must verify **cross-session commit visibility** — i.e. that a
committed write is visible from an entirely separate session.  This cannot
be done with the rollback-based isolation that the other test modules use.

Instead, each test in this module:

1. Creates its own ``SqlAlchemyUnitOfWork`` (with its own internal session).
2. Performs operations and either commits or rolls back explicitly.
3. Opens a *second* independent session to verify persistence from the
   outside.
4. Cleans up any rows it inserted via a final ``DELETE`` in a dedicated
   cleanup session, leaving the database in its original state.

Helper fixtures defined here are local (not in the root conftest) because
they deviate from the shared rollback pattern on purpose.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import (
    TicketModel,
)
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.shared.database.session import async_session_factory
from tests.unit.ticket_management.domain.factories import (
    a_moment_after,
    make_ticket,
)


# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------


async def ticket_exists_in_db(ticket_id, session: AsyncSession) -> bool:
    """Query a separate session to check if a ticket row exists."""
    stmt = select(TicketModel).where(TicketModel.id == ticket_id)
    result = await session.scalar(stmt)
    return result is not None


async def delete_ticket_from_db(ticket_id) -> None:
    """Hard-delete a ticket row to clean up after a commit-based test."""
    async with async_session_factory() as session:
        stmt = select(TicketModel).where(TicketModel.id == ticket_id)
        model = await session.scalar(stmt)
        if model is not None:
            await session.delete(model)
            await session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUoWRepositoryAccess:
    async def test_uow_exposes_tickets_repository(self):
        # Arrange / Act
        async with SqlAlchemyUnitOfWork() as uow:
            # Assert
            assert uow.tickets is not None
            assert isinstance(uow.tickets, SqlAlchemyTicketRepository)


class TestCommit:
    async def test_commit_persists_ticket_across_sessions(self):
        # Arrange
        ticket = make_ticket()

        # Act — commit inside UoW
        async with SqlAlchemyUnitOfWork() as uow:
            await uow.tickets.add(ticket)
            await uow.commit()

        # Assert — verify from a second independent session
        try:
            async with async_session_factory() as verify_session:
                exists = await ticket_exists_in_db(ticket.id, verify_session)
            assert exists is True
        finally:
            await delete_ticket_from_db(ticket.id)

    async def test_multiple_adds_in_single_commit(self):
        # Arrange
        t1 = make_ticket()
        t2 = make_ticket()

        # Act
        async with SqlAlchemyUnitOfWork() as uow:
            await uow.tickets.add(t1)
            await uow.tickets.add(t2)
            await uow.commit()

        # Assert
        try:
            async with async_session_factory() as verify_session:
                exists_1 = await ticket_exists_in_db(t1.id, verify_session)
                exists_2 = await ticket_exists_in_db(t2.id, verify_session)
            assert exists_1 is True
            assert exists_2 is True
        finally:
            await delete_ticket_from_db(t1.id)
            await delete_ticket_from_db(t2.id)


class TestRollback:
    async def test_explicit_rollback_discards_changes(self):
        # Arrange
        ticket = make_ticket()

        # Act — add then roll back
        uow = SqlAlchemyUnitOfWork()
        async with uow:
            await uow.tickets.add(ticket)
            await uow.rollback()
            # Do NOT commit

        # Assert — ticket must not be in the DB
        async with async_session_factory() as verify_session:
            exists = await ticket_exists_in_db(ticket.id, verify_session)
        assert exists is False

    async def test_exception_in_context_manager_triggers_rollback(self):
        # Arrange
        ticket = make_ticket()

        # Act — exception inside async with
        with pytest.raises(RuntimeError, match="intentional"):
            async with SqlAlchemyUnitOfWork() as uow:
                await uow.tickets.add(ticket)
                raise RuntimeError("intentional")

        # Assert — no commit happened; ticket absent
        async with async_session_factory() as verify_session:
            exists = await ticket_exists_in_db(ticket.id, verify_session)
        assert exists is False

    async def test_no_commit_means_no_persistence(self):
        """Exiting the context manager without committing discards changes."""
        # Arrange
        ticket = make_ticket()

        # Act — exit without commit (no exception, just no commit call)
        async with SqlAlchemyUnitOfWork() as uow:
            await uow.tickets.add(ticket)
            # No commit

        # Assert
        async with async_session_factory() as verify_session:
            exists = await ticket_exists_in_db(ticket.id, verify_session)
        assert exists is False


class TestContextManagerLifecycle:
    async def test_context_manager_returns_uow_instance(self):
        # Act
        async with SqlAlchemyUnitOfWork() as uow:
            # Assert — __aenter__ must return the UoW itself
            assert isinstance(uow, SqlAlchemyUnitOfWork)

    async def test_session_is_closed_after_context_exit(self):
        # Arrange
        uow = SqlAlchemyUnitOfWork()

        # Act
        async with uow:
            session = uow.session

        # Assert — after __aexit__, the session is closed (is_active is False)
        assert not session.is_active
