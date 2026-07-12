from __future__ import annotations

import pytest

from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from tests.unit.ticket_management.application import dto_factories
from tests.unit.ticket_management.domain import factories


class TestGetTicketHandler:
	@pytest.mark.asyncio
	async def test_returns_the_ticket_detail_dto_for_an_existing_ticket(self, read_repository):
		detail = dto_factories.make_detail_dto(title="Payment gateway returns 500")
		read_repository.seed_ticket(detail)
		handler = GetTicketHandler(read_repository)

		result = await handler.handle(GetTicketQuery(ticket_id=detail.id))

		# The handler is pure delegation + not-found translation: whatever
		# the read repository returns should come back unchanged.
		assert result is detail

	@pytest.mark.asyncio
	async def test_passes_the_requested_ticket_id_to_the_repository(self, read_repository):
		detail = dto_factories.make_detail_dto()
		read_repository.seed_ticket(detail)
		handler = GetTicketHandler(read_repository)

		await handler.handle(GetTicketQuery(ticket_id=detail.id))

		assert read_repository.received_get_ticket_id == detail.id

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_the_repository_returns_none(self, read_repository):
		# GetTicketHandler is the one query handler with actual logic: it
		# translates a missing read model (None) into the application-level
		# TicketNotFound exception, matching how the command handlers behave
		# for the same case.
		handler = GetTicketHandler(read_repository)

		with pytest.raises(TicketNotFound):
			await handler.handle(GetTicketQuery(ticket_id=factories.new_uuid()))

	@pytest.mark.asyncio
	async def test_does_not_return_a_ticket_that_was_never_seeded(self, read_repository):
		other_ticket = dto_factories.make_detail_dto()
		read_repository.seed_ticket(other_ticket)
		handler = GetTicketHandler(read_repository)

		with pytest.raises(TicketNotFound):
			await handler.handle(GetTicketQuery(ticket_id=factories.new_uuid()))
