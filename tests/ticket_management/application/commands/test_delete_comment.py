from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.delete_comment.command import DeleteCommentCommand
from app.modules.ticket_management.application.commands.delete_comment.handler import DeleteCommentHandler
from app.modules.ticket_management.application.exceptions import CommentNotFound, TicketNotFound
from app.modules.ticket_management.domain.events.comment_deleted import CommentDeleted
from tests.ticket_management.domain import factories


class TestDeleteCommentHandler:
	@pytest.mark.asyncio
	async def test_marks_the_comment_deleted(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = DeleteCommentHandler(uow, event_publisher)

		await handler.handle(DeleteCommentCommand(ticket_id=ticket.id, comment_id=comment.id, deleted_at=moment))

		assert comment.deleted_at == moment
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_comment_deleted(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = DeleteCommentHandler(uow, event_publisher)

		await handler.handle(DeleteCommentCommand(ticket_id=ticket.id, comment_id=comment.id, deleted_at=moment))

		assert event_publisher.last == CommentDeleted(ticket_id=ticket.id, comment_id=comment.id, deleted_at=moment)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = DeleteCommentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(DeleteCommentCommand(ticket_id=factories.new_uuid(), comment_id=factories.new_uuid(), deleted_at=factories.BASE_TIME))

	@pytest.mark.asyncio
	async def test_translates_domain_comment_not_found_to_application_exception(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = DeleteCommentHandler(uow, event_publisher)

		with pytest.raises(CommentNotFound):
			await handler.handle(
				DeleteCommentCommand(ticket_id=ticket.id, comment_id=factories.new_uuid(), deleted_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.committed is False
		assert event_publisher.published == []
