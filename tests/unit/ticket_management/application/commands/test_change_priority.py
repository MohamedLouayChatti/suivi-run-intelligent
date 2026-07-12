from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.change_priority.command import ChangePriorityCommand
from app.modules.ticket_management.application.commands.change_priority.handler import ChangePriorityHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.events.priority_changed import PriorityChanged
from app.modules.ticket_management.domain.exceptions import TicketClosed
from tests.unit.ticket_management.domain import factories


class TestChangePriorityHandler:
	@pytest.mark.asyncio
	async def test_changes_the_priority_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket(priority=Priority.LOW))
		handler = ChangePriorityHandler(uow, event_publisher)

		await handler.handle(
			ChangePriorityCommand(ticket_id=ticket.id, priority=Priority.CRITICAL, changed_at=factories.a_moment_after(ticket.updated_at))
		)

		assert ticket.priority == Priority.CRITICAL
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_priority_changed_with_old_and_new_priority(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket(priority=Priority.LOW))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ChangePriorityHandler(uow, event_publisher)

		await handler.handle(ChangePriorityCommand(ticket_id=ticket.id, priority=Priority.HIGH, changed_at=moment))

		assert event_publisher.last == PriorityChanged(
			ticket_id=ticket.id, old_priority=Priority.LOW, new_priority=Priority.HIGH, changed_at=moment
		)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = ChangePriorityHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(ChangePriorityCommand(ticket_id=factories.new_uuid(), priority=Priority.HIGH, changed_at=factories.BASE_TIME))

	@pytest.mark.asyncio
	async def test_domain_rule_violations_propagate_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_closed_ticket())
		handler = ChangePriorityHandler(uow, event_publisher)

		with pytest.raises(TicketClosed):
			await handler.handle(
				ChangePriorityCommand(ticket_id=ticket.id, priority=Priority.HIGH, changed_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.committed is False
		assert event_publisher.published == []
