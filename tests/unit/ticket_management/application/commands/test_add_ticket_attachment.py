from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.add_ticket_attachment.command import AddTicketAttachmentCommand
from app.modules.ticket_management.application.commands.add_ticket_attachment.handler import AddTicketAttachmentHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from app.modules.ticket_management.domain.exceptions import DuplicateAttachment
from tests.unit.ticket_management.domain import factories


def _command(ticket_id, **overrides) -> AddTicketAttachmentCommand:
	return AddTicketAttachmentCommand(
		ticket_id=ticket_id,
		attachment_id=factories.new_uuid(),
		filename="log.txt",
		content_type="text/plain",
		storage_path="s3://bucket/log.txt",
		uploaded_by=factories.new_uuid(),
		uploaded_at=factories.BASE_TIME,
	)


class TestAddTicketAttachmentHandler:
	@pytest.mark.asyncio
	async def test_attaches_the_file_to_the_ticket(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = AddTicketAttachmentHandler(uow, event_publisher)

		await handler.handle(_command(ticket.id))

		assert len(ticket.attachments) == 1
		assert ticket.attachments[0].filename == "log.txt"
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_attachment_added(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		command = _command(ticket.id)
		handler = AddTicketAttachmentHandler(uow, event_publisher)

		await handler.handle(command)

		assert event_publisher.last == AttachmentAdded(
			ticket_id=ticket.id, attachment_id=command.attachment_id, uploaded_by=command.uploaded_by, uploaded_at=command.uploaded_at
		)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = AddTicketAttachmentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(_command(factories.new_uuid()))

	@pytest.mark.asyncio
	async def test_duplicate_attachment_propagates_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		existing = factories.make_attachment()
		ticket.add_attachment(existing, factories.a_moment_after(ticket.updated_at))
		handler = AddTicketAttachmentHandler(uow, event_publisher)

		with pytest.raises(DuplicateAttachment):
			await handler.handle(_command(ticket.id, attachment_id=existing.id))

		assert uow.committed is False
		assert event_publisher.published == []
