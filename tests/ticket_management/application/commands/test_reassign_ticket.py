from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.reassign_ticket.command import ReassignTicketCommand
from app.modules.ticket_management.application.commands.reassign_ticket.handler import ReassignTicketHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.events.ticket_reassigned import TicketReassigned
from app.modules.ticket_management.domain.exceptions import TicketNotAssigned
from tests.ticket_management.domain import factories


class TestReassignTicketHandler:
	async def test_reassigns_the_ticket_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_assigned_ticket())
		new_assignee = factories.new_uuid()
		handler = ReassignTicketHandler(uow, event_publisher)

		await handler.handle(
			ReassignTicketCommand(ticket_id=ticket.id, assignee_id=new_assignee, reassigned_at=factories.a_moment_after(ticket.updated_at))
		)

		assert ticket.assignee_id == new_assignee
		assert ticket in ticket_repository.saved
		assert uow.committed is True

	async def test_publishes_ticket_reassigned(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_assigned_ticket())
		new_assignee = factories.new_uuid()
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ReassignTicketHandler(uow, event_publisher)

		await handler.handle(ReassignTicketCommand(ticket_id=ticket.id, assignee_id=new_assignee, reassigned_at=moment))

		assert event_publisher.last == TicketReassigned(ticket_id=ticket.id, assignee_id=new_assignee, reassigned_at=moment)

	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = ReassignTicketHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(
				ReassignTicketCommand(ticket_id=factories.new_uuid(), assignee_id=factories.new_uuid(), reassigned_at=factories.BASE_TIME)
			)

	async def test_domain_rule_violations_propagate_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())  # unassigned
		handler = ReassignTicketHandler(uow, event_publisher)

		with pytest.raises(TicketNotAssigned):
			await handler.handle(
				ReassignTicketCommand(ticket_id=ticket.id, assignee_id=factories.new_uuid(), reassigned_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.committed is False
		assert event_publisher.published == []
