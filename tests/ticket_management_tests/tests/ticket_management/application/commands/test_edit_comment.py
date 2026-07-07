from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.edit_comment.command import EditCommentCommand
from app.modules.ticket_management.application.commands.edit_comment.handler import EditCommentHandler
from app.modules.ticket_management.application.exceptions import CommentNotFound, TicketNotFound
from app.modules.ticket_management.domain.events.comment_edited import CommentEdited
from tests.ticket_management.domain import factories


class TestEditCommentHandler:
	async def test_edits_the_comment_content(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		handler = EditCommentHandler(uow, event_publisher)

		await handler.handle(
			EditCommentCommand(ticket_id=ticket.id, comment_id=comment.id, content="Corrected root cause", edited_at=factories.a_moment_after(ticket.updated_at))
		)

		assert comment.content == "Corrected root cause"
		assert uow.committed is True

	async def test_publishes_comment_edited(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		comment = factories.make_comment()
		ticket.add_comment(comment, factories.a_moment_after(ticket.updated_at))
		moment = factories.a_moment_after(ticket.updated_at)
		handler = EditCommentHandler(uow, event_publisher)

		await handler.handle(EditCommentCommand(ticket_id=ticket.id, comment_id=comment.id, content="Updated", edited_at=moment))

		assert event_publisher.last == CommentEdited(ticket_id=ticket.id, comment_id=comment.id, edited_at=moment)

	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = EditCommentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(EditCommentCommand(ticket_id=factories.new_uuid(), comment_id=factories.new_uuid(), content="x", edited_at=factories.BASE_TIME))

	async def test_translates_domain_comment_not_found_to_application_exception(self, uow, event_publisher, ticket_repository):
		# The handler catches the domain-layer CommentNotFound and re-raises
		# the application-layer CommentNotFound, keeping the domain exception
		# vocabulary out of the application boundary.
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = EditCommentHandler(uow, event_publisher)

		with pytest.raises(CommentNotFound):
			await handler.handle(
				EditCommentCommand(ticket_id=ticket.id, comment_id=factories.new_uuid(), content="x", edited_at=factories.a_moment_after(ticket.updated_at))
			)

		assert uow.committed is False
		assert event_publisher.published == []
