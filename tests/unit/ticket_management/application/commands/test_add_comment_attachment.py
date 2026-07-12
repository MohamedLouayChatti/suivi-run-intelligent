from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.add_comment_attachment.command import AddCommentAttachmentCommand
from app.modules.ticket_management.application.commands.add_comment_attachment.handler import AddCommentAttachmentHandler
from app.modules.ticket_management.application.exceptions import CommentNotFound, TicketNotFound
from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from tests.unit.ticket_management.domain import factories


def _command(ticket_id, comment_id, **overrides) -> AddCommentAttachmentCommand:
	return AddCommentAttachmentCommand(
		ticket_id=ticket_id,
		comment_id=comment_id,
		attachment_id=factories.new_uuid(),
		filename="screenshot.png",
		content_type="image/png",
		storage_path="s3://bucket/screenshot.png",
		uploaded_by=factories.new_uuid(),
		uploaded_at=factories.BASE_TIME,
	)


class TestAddCommentAttachmentHandler:
	@pytest.mark.asyncio
	async def test_attaches_the_file_to_the_comment(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		handler = AddCommentAttachmentHandler(uow, event_publisher)

		await handler.handle(_command(ticket.id, comment.id))

		assert len(comment.attachments) == 1
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_attachment_added(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		command = _command(ticket.id, comment.id)
		handler = AddCommentAttachmentHandler(uow, event_publisher)

		await handler.handle(command)

		assert event_publisher.last == AttachmentAdded(
			ticket_id=ticket.id, attachment_id=command.attachment_id, uploaded_by=command.uploaded_by, uploaded_at=command.uploaded_at
		)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = AddCommentAttachmentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(_command(factories.new_uuid(), factories.new_uuid()))

	@pytest.mark.asyncio
	async def test_translates_domain_comment_not_found_to_application_exception(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = AddCommentAttachmentHandler(uow, event_publisher)

		with pytest.raises(CommentNotFound):
			await handler.handle(_command(ticket.id, factories.new_uuid()))

		assert uow.committed is False
		assert event_publisher.published == []
