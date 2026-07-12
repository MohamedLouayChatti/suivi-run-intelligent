from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.delete_ticket_attachment.command import DeleteTicketAttachmentCommand
from app.modules.ticket_management.application.commands.delete_ticket_attachment.handler import DeleteTicketAttachmentHandler
from app.modules.ticket_management.application.exceptions import AttachmentNotFound, TicketNotFound
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted
from tests.unit.ticket_management.domain import factories


class TestDeleteTicketAttachmentHandler:
	@pytest.mark.asyncio
	async def test_marks_the_attachment_deleted(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		attachment = factories.make_attachment()
		ticket.add_attachment(attachment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = DeleteTicketAttachmentHandler(uow, event_publisher)

		await handler.handle(DeleteTicketAttachmentCommand(ticket_id=ticket.id, attachment_id=attachment.id, deleted_at=moment))

		assert attachment.deleted_at == moment
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_attachment_deleted(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		attachment = factories.make_attachment()
		ticket.add_attachment(attachment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = DeleteTicketAttachmentHandler(uow, event_publisher)

		await handler.handle(DeleteTicketAttachmentCommand(ticket_id=ticket.id, attachment_id=attachment.id, deleted_at=moment))

		assert event_publisher.last == AttachmentDeleted(ticket_id=ticket.id, attachment_id=attachment.id, deleted_at=moment)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = DeleteTicketAttachmentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(DeleteTicketAttachmentCommand(ticket_id=factories.new_uuid(), attachment_id=factories.new_uuid(), deleted_at=factories.BASE_TIME))

	@pytest.mark.asyncio
	async def test_raises_application_attachment_not_found_when_attachment_is_missing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = DeleteTicketAttachmentHandler(uow, event_publisher)

		with pytest.raises(AttachmentNotFound):
			await handler.handle(
				DeleteTicketAttachmentCommand(ticket_id=ticket.id, attachment_id=factories.new_uuid(), deleted_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.committed is False
		assert event_publisher.published == []
