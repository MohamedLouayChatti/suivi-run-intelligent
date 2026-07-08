from __future__ import annotations

import pytest

from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from tests.ticket_management.application import dto_factories
from tests.ticket_management.domain import factories


class TestListTicketsHandler:
	"""
	ListTicketsHandler has no logic of its own: `handle` is a single
	pass-through call to `read_repository.list_tickets(query)`. Filtering,
	pagination, and archived-ticket exclusion are all implemented by
	whatever backs `TicketReadRepository` (SQL, in-memory, etc.), which
	doesn't exist yet in this codebase. These tests therefore verify only
	the orchestration contract: the query reaches the repository intact,
	and the repository's result comes back out unchanged. They intentionally
	do NOT assert on filtering semantics, since asserting on behavior that
	isn't implemented anywhere would be testing an assumption, not the code.
	"""

	@pytest.mark.asyncio
	async def test_returns_whatever_the_repository_returns(self, read_repository):
		summaries = [dto_factories.make_summary_dto(), dto_factories.make_summary_dto()]
		read_repository.list_tickets_result = summaries
		handler = ListTicketsHandler(read_repository)

		result = await handler.handle(ListTicketsQuery())

		assert result is summaries

	@pytest.mark.asyncio
	async def test_returns_an_empty_list_when_the_repository_has_no_matches(self, read_repository):
		handler = ListTicketsHandler(read_repository)

		result = await handler.handle(ListTicketsQuery())

		assert result == []

	@pytest.mark.asyncio
	async def test_passes_the_query_object_to_the_repository_unchanged(self, read_repository):
		query = ListTicketsQuery(
			application=Application.APP_2,
			status=Status.IN_PROGRESS,
			priority=Priority.HIGH,
			assignee_id=factories.new_uuid(),
			include_archived=True,
			limit=25,
			offset=50,
		)
		handler = ListTicketsHandler(read_repository)

		await handler.handle(query)

		assert read_repository.received_list_query is query

	@pytest.mark.asyncio
	async def test_default_query_uses_documented_defaults(self):
		# Pins the documented default filter/pagination values on the query
		# DTO itself (no filters, archived tickets excluded, first 100).
		query = ListTicketsQuery()

		assert query.application is None
		assert query.status is None
		assert query.priority is None
		assert query.assignee_id is None
		assert query.include_archived is False
		assert query.limit == 100
		assert query.offset == 0
