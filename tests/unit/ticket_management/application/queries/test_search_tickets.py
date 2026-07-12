from __future__ import annotations

import pytest

from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from tests.unit.ticket_management.application import dto_factories
from tests.unit.ticket_management.domain import factories


class TestSearchTicketsHandler:
	"""
	Like ListTicketsHandler, SearchTicketsHandler is pure delegation to
	`read_repository.search_tickets(query)`. The actual text-matching logic
	behind `term` is an Infrastructure concern that hasn't been built yet,
	so these tests only cover the handler's own contract: correct
	delegation of the query and pass-through of the result.
	"""

	@pytest.mark.asyncio
	async def test_returns_whatever_the_repository_returns(self, read_repository):
		summaries = [dto_factories.make_summary_dto(title="Checkout fails with 500")]
		read_repository.search_tickets_result = summaries
		handler = SearchTicketsHandler(read_repository)

		result = await handler.handle(SearchTicketsQuery(term="checkout"))

		assert result is summaries

	@pytest.mark.asyncio
	async def test_returns_an_empty_list_when_nothing_matches(self, read_repository):
		handler = SearchTicketsHandler(read_repository)

		result = await handler.handle(SearchTicketsQuery(term="nonexistent term"))

		assert result == []

	@pytest.mark.asyncio
	async def test_passes_the_query_object_to_the_repository_unchanged(self, read_repository):
		query = SearchTicketsQuery(
			term="timeout",
			application=Application.APP_3,
			status=Status.OPEN,
			priority=Priority.CRITICAL,
			assignee_id=factories.new_uuid(),
			include_archived=True,
			limit=10,
			offset=5,
		)
		handler = SearchTicketsHandler(read_repository)

		await handler.handle(query)

		assert read_repository.received_search_query is query

	@pytest.mark.asyncio
	async def test_default_query_uses_documented_defaults(self):
		# `term` has no default (it's the one required field); everything
		# else mirrors ListTicketsQuery's defaults except for a smaller page size.
		query = SearchTicketsQuery(term="checkout")

		assert query.term == "checkout"
		assert query.application is None
		assert query.status is None
		assert query.priority is None
		assert query.assignee_id is None
		assert query.include_archived is False
		assert query.limit == 50
		assert query.offset == 0
