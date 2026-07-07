from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.delete_comment_attachment.command import DeleteCommentAttachmentCommand
from app.modules.ticket_management.application.commands.delete_comment_attachment.handler import DeleteCommentAttachmentHandler
from app.modules.ticket_management.application.exceptions import AttachmentNotFound, CommentNotFound, TicketNotFound
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted
from tests.ticket_management.domain import factories


class TestDeleteCommentAttachmentHandler:
	async def test_marks_the_comment_attachment_deleted(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		attachment = factories.make_attachment()
		ticket.add_attachment_to_comment(comment.id, attachment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = DeleteCommentAttachmentHandler(uow, event_publisher)

		await handler.handle(
			DeleteCommentAttachmentCommand(ticket_id=ticket.id, comment_id=comment.id, attachment_id=attachment.id, deleted_at=moment)
		)

		assert attachment.deleted_at == moment
		assert uow.committed is True

	async def test_publishes_attachment_deleted(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		attachment = factories.make_attachment()
		ticket.add_attachment_to_comment(comment.id, attachment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = DeleteCommentAttachmentHandler(uow, event_publisher)

		await handler.handle(
			DeleteCommentAttachmentCommand(ticket_id=ticket.id, comment_id=comment.id, attachment_id=attachment.id, deleted_at=moment)
		)

		assert event_publisher.last == AttachmentDeleted(ticket_id=ticket.id, attachment_id=attachment.id, deleted_at=moment)

	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = DeleteCommentAttachmentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(
				DeleteCommentAttachmentCommand(
					ticket_id=factories.new_uuid(), comment_id=factories.new_uuid(), attachment_id=factories.new_uuid(), deleted_at=factories.BASE_TIME
				)
			)

	async def test_translates_domain_comment_not_found_to_application_exception(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = DeleteCommentAttachmentHandler(uow, event_publisher)

		with pytest.raises(CommentNotFound):
			await handler.handle(
				DeleteCommentAttachmentCommand(
					ticket_id=ticket.id, comment_id=factories.new_uuid(), attachment_id=factories.new_uuid(), deleted_at=factories.a_moment_after(ticket.updated_at)
				)
			)

		assert uow.committed is False
		assert event_publisher.published == []

	async def test_translates_domain_attachment_not_found_to_application_exception(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		handler = DeleteCommentAttachmentHandler(uow, event_publisher)

		with pytest.raises(AttachmentNotFound):
			await handler.handle(
				DeleteCommentAttachmentCommand(
					ticket_id=ticket.id, comment_id=comment.id, attachment_id=factories.new_uuid(), deleted_at=factories.a_moment_after(ticket.updated_at)
				)
			)

		assert uow.committed is False
		assert event_publisher.published == []
