from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.add_comment.command import AddCommentCommand
from app.modules.ticket_management.application.commands.add_comment.handler import AddCommentHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.events.comment_added import CommentAdded
from app.modules.ticket_management.domain.exceptions import EmptyComment
from tests.unit.ticket_management.domain import factories


def _command(ticket_id, **overrides) -> AddCommentCommand:
	return AddCommentCommand(
		ticket_id=ticket_id,
		comment_id=factories.new_uuid(),
		author_id=factories.new_uuid(),
		content="Reproduced locally, investigating.",
		created_at=factories.BASE_TIME,
	)

class TestAddCommentHandler:
	@pytest.mark.asyncio
	async def test_adds_the_comment_to_the_ticket_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = AddCommentHandler(uow, event_publisher)

		result = await handler.handle(_command(ticket.id))

		assert len(ticket.comments) == 1
		assert ticket.comments[0].content == "Reproduced locally, investigating."
		assert result.comments[0].content == "Reproduced locally, investigating."
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_comment_added(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		command = _command(ticket.id)
		handler = AddCommentHandler(uow, event_publisher)

		await handler.handle(command)

		assert event_publisher.last == CommentAdded(
			ticket_id=ticket.id, comment_id=command.comment_id, author_id=command.author_id, created_at=command.created_at
		)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = AddCommentHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(_command(factories.new_uuid()))

	@pytest.mark.asyncio
	async def test_blank_content_raises_and_does_not_commit(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = AddCommentHandler(uow, event_publisher)

		with pytest.raises(EmptyComment):
			await handler.handle(_command(ticket.id, content="   "))

		assert uow.committed is False
		assert event_publisher.published == []
