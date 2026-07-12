from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import CommentNotFound, TicketClosed
from tests.unit.ticket_management.domain import factories


class TestAddComment:
	def test_appends_a_comment_and_stamps_updated_at(self, open_ticket, comment):
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.add_comment(comment, moment)

		assert comment in open_ticket.comments
		assert open_ticket.updated_at == moment

	def test_cannot_comment_on_a_closed_ticket(self, closed_ticket, comment):
		with pytest.raises(TicketClosed):
			closed_ticket.add_comment(comment, factories.a_moment_after(closed_ticket.updated_at))


class TestEditComment:
	def test_edits_an_existing_comment(self, open_ticket, comment):
		open_ticket.add_comment(comment, factories.a_moment_after(open_ticket.updated_at))
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.edit_comment(comment.id, "Revised content", moment)

		assert comment.content == "Revised content"
		assert open_ticket.updated_at == moment

	def test_raises_when_comment_does_not_exist(self, open_ticket):
		with pytest.raises(CommentNotFound):
			open_ticket.edit_comment(factories.new_uuid(), "content", factories.a_moment_after(open_ticket.updated_at))


class TestDeleteComment:
	def test_deletes_an_existing_comment(self, open_ticket, comment):
		open_ticket.add_comment(comment, factories.a_moment_after(open_ticket.updated_at))
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.delete_comment(comment.id, moment)

		assert comment.deleted_at == moment
		assert open_ticket.updated_at == moment

	def test_raises_when_comment_does_not_exist(self, open_ticket):
		with pytest.raises(CommentNotFound):
			open_ticket.delete_comment(factories.new_uuid(), factories.a_moment_after(open_ticket.updated_at))
