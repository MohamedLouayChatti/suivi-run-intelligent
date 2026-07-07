from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.transfer_application.command import TransferApplicationCommand
from app.modules.ticket_management.application.commands.transfer_application.handler import TransferApplicationHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred
from app.modules.ticket_management.domain.exceptions import SameApplicationTransfer, TicketNotAssigned
from tests.ticket_management.domain import factories


class TestTransferApplicationHandler:
	async def test_transfers_the_ticket_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_assigned_ticket(application=Application.APP_1))
		new_assignee = factories.new_uuid()
		moment = factories.a_moment_after(ticket.updated_at)
		handler = TransferApplicationHandler(uow, event_publisher)

		await handler.handle(
			TransferApplicationCommand(ticket_id=ticket.id, new_application=Application.APP_2, new_assignee=new_assignee, transferred_at=moment)
		)

		assert ticket.application == Application.APP_2
		assert ticket.assignee_id == new_assignee
		assert uow.committed is True

	async def test_publishes_ticket_transferred_with_old_and_new_values(self, uow, event_publisher, ticket_repository):
		old_assignee = factories.new_uuid()
		ticket = ticket_repository.seed(factories.make_assigned_ticket(application=Application.APP_1, assignee_id=old_assignee))
		new_assignee = factories.new_uuid()
		moment = factories.a_moment_after(ticket.updated_at)
		handler = TransferApplicationHandler(uow, event_publisher)

		await handler.handle(
			TransferApplicationCommand(ticket_id=ticket.id, new_application=Application.APP_2, new_assignee=new_assignee, transferred_at=moment)
		)

		assert event_publisher.last == TicketTransferred(
			ticket_id=ticket.id,
			old_application=Application.APP_1,
			new_application=Application.APP_2,
			old_assignee_id=old_assignee,
			new_assignee_id=new_assignee,
			transferred_at=moment,
		)

	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = TransferApplicationHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(
				TransferApplicationCommand(
					ticket_id=factories.new_uuid(), new_application=Application.APP_2, new_assignee=factories.new_uuid(), transferred_at=factories.BASE_TIME
				)
			)

	async def test_transferring_to_the_same_application_propagates_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_assigned_ticket(application=Application.APP_1))
		handler = TransferApplicationHandler(uow, event_publisher)

		with pytest.raises(SameApplicationTransfer):
			await handler.handle(
				TransferApplicationCommand(
					ticket_id=ticket.id, new_application=Application.APP_1, new_assignee=factories.new_uuid(), transferred_at=factories.a_moment_after(ticket.updated_at)
				)
			)

		assert uow.committed is False
		assert event_publisher.published == []

	async def test_transferring_an_unassigned_ticket_propagates_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket(application=Application.APP_1))
		handler = TransferApplicationHandler(uow, event_publisher)

		with pytest.raises(TicketNotAssigned):
			await handler.handle(
				TransferApplicationCommand(
					ticket_id=ticket.id, new_application=Application.APP_2, new_assignee=factories.new_uuid(), transferred_at=factories.a_moment_after(ticket.updated_at)
				)
			)

		assert uow.committed is False
		assert event_publisher.published == []
