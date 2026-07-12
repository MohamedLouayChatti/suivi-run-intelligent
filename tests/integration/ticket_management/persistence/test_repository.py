"""
Integration tests for ``SqlAlchemyTicketRepository``.

These tests run against the real PostgreSQL database.  Each test receives a
fresh ``AsyncSession`` that is rolled back after the test completes, so no
data is permanently written and tests remain independent.

Setup pattern
-------------
1. Build a domain ``Ticket`` (and optionally add comments / attachments).
2. ``await repo.add(ticket)`` — stages the ORM model in the session.
3. ``await session.flush()`` — sends the INSERT to the DB within the
   transaction so we can query within the same session.
4. Assert on what ``repo.get()`` returns.

The session-level rollback (handled by the ``db_session`` fixture) discards
everything after the test.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from tests.unit.ticket_management.domain.factories import (
    BASE_TIME,
    a_moment_after,
    make_attachment,
    make_comment,
    make_ticket,
    new_uuid,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def flush(session: AsyncSession) -> None:
    """Flush pending SQL to DB without committing (stays in the test transaction)."""
    await session.flush()


# ---------------------------------------------------------------------------
# add / get
# ---------------------------------------------------------------------------


class TestAddAndGet:
    async def test_add_and_get_returns_ticket_with_correct_scalar_fields(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket_id = uuid4()
        assignee_id = uuid4()
        ticket = make_ticket(id=ticket_id, assignee_id=assignee_id, priority=Priority.CRITICAL)

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket_id)

        # Assert
        assert result is not None
        assert result.id == ticket_id
        assert result.title == ticket.title
        assert result.description == ticket.description
        assert result.application == Application.APP_1
        assert result.status == Status.OPEN
        assert result.priority == Priority.CRITICAL
        assert result.assignee_id == assignee_id
        assert result.archived_at is None

    async def test_get_nonexistent_ticket_returns_none(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
    ):
        # Act
        result = await ticket_repository.get(uuid4())

        # Assert
        assert result is None

    async def test_uuid_survives_round_trip(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket_id = uuid4()
        ticket = make_ticket(id=ticket_id)

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket_id)

        # Assert
        assert result is not None
        assert result.id == ticket_id
        assert type(result.id) is type(ticket_id)  # must be UUID, not str

    async def test_enum_values_survive_round_trip(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(
            priority=Priority.CRITICAL,
            application=Application.APP_4,
        )
        ticket.start_progress(a_moment_after(ticket.created_at))

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert result.priority == Priority.CRITICAL
        assert result.application == Application.APP_4
        assert result.status == Status.IN_PROGRESS


# ---------------------------------------------------------------------------
# Nested collections
# ---------------------------------------------------------------------------


class TestNestedCollections:
    async def test_add_and_get_ticket_with_comment(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        ticket.add_comment(comment, a_moment_after(ticket.created_at))

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert len(result.comments) == 1
        rc = result.comments[0]
        assert rc.id == comment.id
        assert rc.content == comment.content
        assert rc.author_id == comment.author_id

    async def test_add_and_get_ticket_with_direct_attachment(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        attachment = make_attachment()
        ticket.add_attachment(attachment, a_moment_after(ticket.created_at))

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert len(result.attachments) == 1
        ra = result.attachments[0]
        assert ra.id == attachment.id
        assert ra.filename == attachment.filename
        assert ra.content_type == attachment.content_type
        assert ra.storage_path == attachment.storage_path

    async def test_add_and_get_ticket_with_comment_attachment(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        comment_attachment = make_attachment()
        comment.attachments.append(comment_attachment)
        ticket.add_comment(comment, a_moment_after(ticket.created_at))

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert len(result.comments) == 1
        assert len(result.comments[0].attachments) == 1
        assert result.comments[0].attachments[0].id == comment_attachment.id

    async def test_empty_collections_are_returned_as_empty_lists(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()

        # Act
        await ticket_repository.add(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert result.comments == []
        assert result.attachments == []


# ---------------------------------------------------------------------------
# save (update)
# ---------------------------------------------------------------------------


class TestSave:
    async def test_save_new_ticket_persists_it(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()

        # Act
        await ticket_repository.save(ticket)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert result.id == ticket.id

    async def test_save_existing_ticket_updates_fields(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange — persist initial state
        ticket = make_ticket()
        await ticket_repository.add(ticket)
        await flush(db_session)

        # Act — mutate and save
        ticket.change_priority(Priority.CRITICAL, a_moment_after(ticket.created_at))
        await ticket_repository.save(ticket)
        await flush(db_session)

        result = await ticket_repository.get(ticket.id)

        # Assert — updated field persisted
        assert result is not None
        assert result.priority == Priority.CRITICAL

    async def test_save_adds_new_comment_to_existing_ticket(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        await ticket_repository.add(ticket)
        await flush(db_session)

        # Act — add a comment and save
        comment = make_comment()
        ticket.add_comment(comment, a_moment_after(ticket.created_at))
        await ticket_repository.save(ticket)
        await flush(db_session)

        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert len(result.comments) == 1
        assert result.comments[0].id == comment.id

    async def test_save_archived_ticket_persists_archived_at(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        await ticket_repository.add(ticket)
        await flush(db_session)

        # Act
        archived_at = a_moment_after(ticket.created_at)
        ticket.archive(archived_at)
        await ticket_repository.save(ticket)
        await flush(db_session)

        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is not None
        assert result.archived_at == archived_at


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_removes_ticket(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        await ticket_repository.add(ticket)
        await flush(db_session)

        # Act
        await ticket_repository.delete(ticket.id)
        await flush(db_session)
        result = await ticket_repository.get(ticket.id)

        # Assert
        assert result is None

    async def test_delete_nonexistent_ticket_does_not_raise(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
    ):
        # Act / Assert — must not raise
        await ticket_repository.delete(uuid4())
