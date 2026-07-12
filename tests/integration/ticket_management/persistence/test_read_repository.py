"""
Integration tests for ``SqlAlchemyTicketReadRepository``.

These tests run against the real PostgreSQL database using the same
session-level rollback isolation as the repository tests.

Setup pattern
-------------
1. Persist a ticket via the write repository + ``session.flush()``.
2. Query through the read repository (same session).
3. Assert on returned DTOs.

The session rollback in the ``db_session`` fixture discards everything
after each test.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ticket_management.application.queries.list_tickets.query import (
    ListTicketsQuery,
)
from app.modules.ticket_management.application.queries.search_tickets.query import (
    SearchTicketsQuery,
)
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
    SqlAlchemyTicketReadRepository,
)
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_repository import (
    SqlAlchemyTicketRepository,
)
from tests.unit.ticket_management.domain.factories import (
    a_moment_after,
    make_attachment,
    make_comment,
    make_ticket,
    new_uuid,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def persist(ticket, repo: SqlAlchemyTicketRepository, session: AsyncSession) -> None:
    """Add a ticket and flush so read queries can see it within the transaction."""
    await repo.add(ticket)
    await session.flush()


# ---------------------------------------------------------------------------
# get_ticket
# ---------------------------------------------------------------------------


class TestGetTicket:
    async def test_get_ticket_returns_detail_dto(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        await persist(ticket, ticket_repository, db_session)

        # Act
        dto = await ticket_read_repository.get_ticket(ticket.id)

        # Assert
        assert dto is not None
        assert dto.id == ticket.id
        assert dto.title == ticket.title
        assert dto.description == ticket.description
        assert dto.status == ticket.status
        assert dto.priority == ticket.priority
        assert dto.application == ticket.application

    async def test_get_ticket_not_found_returns_none(
        self,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
    ):
        # Act
        dto = await ticket_read_repository.get_ticket(uuid4())

        # Assert
        assert dto is None

    async def test_get_ticket_includes_comments(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        ticket.add_comment(comment, a_moment_after(ticket.created_at))
        await persist(ticket, ticket_repository, db_session)

        # Act
        dto = await ticket_read_repository.get_ticket(ticket.id)

        # Assert
        assert dto is not None
        assert len(dto.comments) == 1
        assert dto.comments[0].id == comment.id
        assert dto.comments[0].content == comment.content

    async def test_get_ticket_includes_attachments(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        attachment = make_attachment()
        ticket.add_attachment(attachment, a_moment_after(ticket.created_at))
        await persist(ticket, ticket_repository, db_session)

        # Act
        dto = await ticket_read_repository.get_ticket(ticket.id)

        # Assert
        assert dto is not None
        assert len(dto.attachments) == 1
        assert dto.attachments[0].id == attachment.id

    async def test_get_ticket_includes_comment_attachments(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        comment = make_comment()
        comment_attachment = make_attachment()
        comment.attachments.append(comment_attachment)
        ticket.add_comment(comment, a_moment_after(ticket.created_at))
        await persist(ticket, ticket_repository, db_session)

        # Act
        dto = await ticket_read_repository.get_ticket(ticket.id)

        # Assert
        assert dto is not None
        assert len(dto.comments[0].attachments) == 1
        assert dto.comments[0].attachments[0].id == comment_attachment.id


# ---------------------------------------------------------------------------
# list_tickets
# ---------------------------------------------------------------------------


class TestListTickets:
    async def _seed(self, ticket_repository, db_session, **overrides):
        ticket = make_ticket(**overrides)
        await persist(ticket, ticket_repository, db_session)
        return ticket

    async def test_returns_seeded_ticket(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = await self._seed(ticket_repository, db_session)
        query = ListTicketsQuery()

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert — the seeded ticket must be present
        ids = [dto.id for dto in results]
        assert ticket.id in ids

    async def test_filter_by_status(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange — one OPEN ticket
        ticket = make_ticket()
        await persist(ticket, ticket_repository, db_session)
        query = ListTicketsQuery(status=Status.OPEN)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert — all returned tickets must be OPEN
        assert all(dto.status == Status.OPEN for dto in results)
        assert any(dto.id == ticket.id for dto in results)

    async def test_filter_by_priority(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(priority=Priority.CRITICAL)
        await persist(ticket, ticket_repository, db_session)
        query = ListTicketsQuery(priority=Priority.CRITICAL)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert
        assert all(dto.priority == Priority.CRITICAL for dto in results)
        assert any(dto.id == ticket.id for dto in results)

    async def test_filter_by_application(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(application=Application.APP_3)
        await persist(ticket, ticket_repository, db_session)
        query = ListTicketsQuery(application=Application.APP_3)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert
        assert all(dto.application == Application.APP_3 for dto in results)
        assert any(dto.id == ticket.id for dto in results)

    async def test_filter_by_assignee_id(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        assignee_id = uuid4()
        ticket = make_ticket(assignee_id=assignee_id)
        await persist(ticket, ticket_repository, db_session)
        query = ListTicketsQuery(assignee_id=assignee_id)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert
        assert all(dto.assignee_id == assignee_id for dto in results)
        assert any(dto.id == ticket.id for dto in results)

    async def test_excludes_archived_by_default(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        ticket.archive(a_moment_after(ticket.created_at))
        await persist(ticket, ticket_repository, db_session)
        query = ListTicketsQuery(include_archived=False)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert — the archived ticket must not appear
        ids = [dto.id for dto in results]
        assert ticket.id not in ids

    async def test_include_archived_returns_archived_ticket(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket()
        ticket.archive(a_moment_after(ticket.created_at))
        await persist(ticket, ticket_repository, db_session)
        query = ListTicketsQuery(include_archived=True)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert
        ids = [dto.id for dto in results]
        assert ticket.id in ids

    async def test_pagination_limit_respected(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange — seed 3 tickets
        for _ in range(3):
            t = make_ticket()
            await persist(t, ticket_repository, db_session)
        query = ListTicketsQuery(limit=2, offset=0)

        # Act
        results = await ticket_read_repository.list_tickets(query)

        # Assert — at most 2 results
        assert len(results) <= 2

    async def test_pagination_offset_shifts_window(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange — seed 3 uniquely identifiable tickets using a unique assignee
        unique_assignee = uuid4()
        for _ in range(3):
            t = make_ticket(assignee_id=unique_assignee)
            await persist(t, ticket_repository, db_session)

        query_all = ListTicketsQuery(assignee_id=unique_assignee, limit=3, offset=0)
        query_offset = ListTicketsQuery(assignee_id=unique_assignee, limit=3, offset=1)

        # Act
        all_results = await ticket_read_repository.list_tickets(query_all)
        offset_results = await ticket_read_repository.list_tickets(query_offset)

        # Assert — offset window is shorter
        assert len(offset_results) == len(all_results) - 1


# ---------------------------------------------------------------------------
# search_tickets
# ---------------------------------------------------------------------------


class TestSearchTickets:
    async def test_search_by_title_term_matches(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(title="unique-search-term-xyz payment failure")
        await persist(ticket, ticket_repository, db_session)
        query = SearchTicketsQuery(term="unique-search-term-xyz")

        # Act
        results = await ticket_read_repository.search_tickets(query)

        # Assert
        ids = [dto.id for dto in results]
        assert ticket.id in ids

    async def test_search_by_description_term_matches(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(description="rare-description-keyword-abc memory leak detected")
        await persist(ticket, ticket_repository, db_session)
        query = SearchTicketsQuery(term="rare-description-keyword-abc")

        # Act
        results = await ticket_read_repository.search_tickets(query)

        # Assert
        ids = [dto.id for dto in results]
        assert ticket.id in ids

    async def test_search_is_case_insensitive(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(title="CaseInsensitiveQXZ payment gateway")
        await persist(ticket, ticket_repository, db_session)
        query = SearchTicketsQuery(term="caseinsensitiveqxz")

        # Act
        results = await ticket_read_repository.search_tickets(query)

        # Assert
        ids = [dto.id for dto in results]
        assert ticket.id in ids

    async def test_search_no_match_returns_empty(
        self,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
    ):
        # Act
        results = await ticket_read_repository.search_tickets(
            SearchTicketsQuery(term="xyzzy-no-match-ever-zzz")
        )

        # Assert
        assert results == []

    async def test_search_excludes_archived_by_default(
        self,
        ticket_repository: SqlAlchemyTicketRepository,
        ticket_read_repository: SqlAlchemyTicketReadRepository,
        db_session: AsyncSession,
    ):
        # Arrange
        ticket = make_ticket(title="archived-search-term-qrs timeout")
        ticket.archive(a_moment_after(ticket.created_at))
        await persist(ticket, ticket_repository, db_session)
        query = SearchTicketsQuery(term="archived-search-term-qrs", include_archived=False)

        # Act
        results = await ticket_read_repository.search_tickets(query)

        # Assert
        ids = [dto.id for dto in results]
        assert ticket.id not in ids
