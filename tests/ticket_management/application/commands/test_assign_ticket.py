from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.assign_ticket.command import AssignTicketCommand
from app.modules.ticket_management.application.commands.assign_ticket.handler import AssignTicketHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.events.ticket_assigned import TicketAssigned
from app.modules.ticket_management.domain.exceptions import TicketAlreadyAssigned
from tests.ticket_management.domain import factories


class TestAssignTicketHandler:
	@pytest.mark.asyncio
	async def test_assigns_the_ticket_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		assignee_id = factories.new_uuid()
		handler = AssignTicketHandler(uow, event_publisher)

		await handler.handle(
			AssignTicketCommand(ticket_id=ticket.id, assignee_id=assignee_id, assigned_at=factories.a_moment_after(ticket.updated_at))
		)

		assert ticket.assignee_id == assignee_id
		assert ticket in ticket_repository.saved
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_ticket_assigned(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		assignee_id = factories.new_uuid()
		moment = factories.a_moment_after(ticket.updated_at)
		handler = AssignTicketHandler(uow, event_publisher)

		await handler.handle(AssignTicketCommand(ticket_id=ticket.id, assignee_id=assignee_id, assigned_at=moment))

		assert event_publisher.last == TicketAssigned(ticket_id=ticket.id, assignee_id=assignee_id, assigned_at=moment)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = AssignTicketHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(
				AssignTicketCommand(ticket_id=factories.new_uuid(), assignee_id=factories.new_uuid(), assigned_at=factories.BASE_TIME)
			)

		assert uow.committed is False
		assert event_publisher.published == []

	@pytest.mark.asyncio
	async def test_domain_rule_violations_propagate_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_assigned_ticket())
		handler = AssignTicketHandler(uow, event_publisher)

		with pytest.raises(TicketAlreadyAssigned):
			await handler.handle(
				AssignTicketCommand(ticket_id=ticket.id, assignee_id=factories.new_uuid(), assigned_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.committed is False
		assert event_publisher.published == []

	@pytest.mark.asyncio
	async def test_rolls_back_and_reraises_when_commit_fails(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		uow.fail_commit_with = RuntimeError("connection lost")
		handler = AssignTicketHandler(uow, event_publisher)

		with pytest.raises(RuntimeError, match="connection lost"):
			await handler.handle(
				AssignTicketCommand(ticket_id=ticket.id, assignee_id=factories.new_uuid(), assigned_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.rolled_back is True
		assert event_publisher.published == []
