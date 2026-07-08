from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.create_ticket.command import CreateTicketCommand
from app.modules.ticket_management.application.commands.create_ticket.handler import CreateTicketHandler
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.modules.ticket_management.domain.exceptions import EmptyTitle
from tests.ticket_management.domain import factories


def _command(**overrides) -> CreateTicketCommand:
	defaults = dict(
		ticket_id=factories.new_uuid(),
		title="Login page throws 500",
		description="Users cannot log in since 09:00 UTC.",
		priority=Priority.HIGH,
		created_at=factories.BASE_TIME,
		application=Application.APP_1,
		assignee_id=None,
	)
	defaults.update(overrides)
	return CreateTicketCommand(**defaults)


class TestCreateTicketHandler:
	@pytest.mark.asyncio
	async def test_persists_a_new_ticket_via_the_repository(self, uow, event_publisher, ticket_repository):
		handler = CreateTicketHandler(uow, event_publisher)

		await handler.handle(_command())

		assert len(ticket_repository.added) == 1
		persisted = ticket_repository.added[0]
		assert isinstance(persisted, Ticket)
		assert persisted.status == Status.OPEN

	@pytest.mark.asyncio
	async def test_commits_the_unit_of_work(self, uow, event_publisher):
		handler = CreateTicketHandler(uow, event_publisher)

		await handler.handle(_command())

		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_ticket_created_with_the_new_ticket_data(self, uow, event_publisher):
		command = _command(title="Payment gateway down")
		handler = CreateTicketHandler(uow, event_publisher)

		result = await handler.handle(command)

		assert event_publisher.published == [
			TicketCreated(
				ticket_id=result.id,
				title="Payment gateway down",
				description=command.description,
				status=Status.OPEN,
				priority=command.priority,
				created_at=command.created_at,
			)
		]

	@pytest.mark.asyncio
	async def test_returns_a_dto_reflecting_the_created_ticket(self, uow, event_publisher):
		command = _command()
		handler = CreateTicketHandler(uow, event_publisher)

		result = await handler.handle(command)

		assert result.id == command.ticket_id
		assert result.title == command.title
		assert result.status == Status.OPEN

	@pytest.mark.asyncio
	async def test_domain_validation_errors_propagate_and_nothing_is_committed(self, uow, event_publisher):
		# The handler performs no validation of its own; Ticket.create's
		# guard clauses are the only thing standing between a bad command and
		# a persisted ticket. This test confirms that failure path.
		handler = CreateTicketHandler(uow, event_publisher)

		with pytest.raises(EmptyTitle):
			await handler.handle(_command(title="   "))

		assert uow.committed is False
		assert event_publisher.published == []

	@pytest.mark.asyncio
	async def test_rolls_back_and_reraises_when_commit_fails(self, uow, event_publisher):
		uow.fail_commit_with = RuntimeError("database is unreachable")
		handler = CreateTicketHandler(uow, event_publisher)

		with pytest.raises(RuntimeError, match="database is unreachable"):
			await handler.handle(_command())

		assert uow.rolled_back is True
		# The event must never be published for a transaction that didn't commit.
		assert event_publisher.published == []
