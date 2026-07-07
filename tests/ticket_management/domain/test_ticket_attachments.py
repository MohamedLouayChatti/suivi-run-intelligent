from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import (
	AttachmentNotFound,
	CommentNotFound,
	DuplicateAttachment,
	TicketClosed,
)
from tests.ticket_management.domain import factories


class TestAddTicketAttachment:
	def test_appends_an_attachment_and_stamps_updated_at(self, open_ticket, attachment):
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.add_attachment(attachment, moment)

		assert attachment in open_ticket.attachments
		assert open_ticket.updated_at == moment

	def test_cannot_add_the_same_attachment_twice(self, open_ticket, attachment):
		open_ticket.add_attachment(attachment, factories.a_moment_after(open_ticket.updated_at))

		with pytest.raises(DuplicateAttachment):
			open_ticket.add_attachment(attachment, factories.a_moment_after(open_ticket.updated_at))

	def test_cannot_add_an_attachment_to_a_closed_ticket(self, closed_ticket, attachment):
		with pytest.raises(TicketClosed):
			closed_ticket.add_attachment(attachment, factories.a_moment_after(closed_ticket.updated_at))


class TestCommentAttachmentOrchestration:
	def test_adds_an_attachment_to_an_existing_comment(self, open_ticket, comment, attachment):
		open_ticket.add_comment(comment, factories.a_moment_after(open_ticket.updated_at))
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.add_attachment_to_comment(comment.id, attachment, moment)

		assert attachment in comment.attachments
		assert open_ticket.updated_at == moment

	def test_raises_when_comment_does_not_exist(self, open_ticket, attachment):
		with pytest.raises(CommentNotFound):
			open_ticket.add_attachment_to_comment(
				factories.new_uuid(), attachment, factories.a_moment_after(open_ticket.updated_at)
			)

	def test_deletes_an_attachment_from_a_comment(self, open_ticket, comment, attachment):
		open_ticket.add_comment(comment, factories.a_moment_after(open_ticket.updated_at))
		open_ticket.add_attachment_to_comment(comment.id, attachment, factories.a_moment_after(open_ticket.updated_at))
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.delete_attachment_from_comment(comment.id, attachment.id, moment)

		assert attachment.deleted_at == moment
		assert open_ticket.updated_at == moment

	def test_raises_when_comment_does_not_exist_for_deletion(self, open_ticket):
		with pytest.raises(CommentNotFound):
			open_ticket.delete_attachment_from_comment(
				factories.new_uuid(), factories.new_uuid(), factories.a_moment_after(open_ticket.updated_at)
			)

	def test_raises_when_attachment_does_not_exist_on_comment(self, open_ticket, comment):
		open_ticket.add_comment(comment, factories.a_moment_after(open_ticket.updated_at))

		with pytest.raises(AttachmentNotFound):
			open_ticket.delete_attachment_from_comment(
				comment.id, factories.new_uuid(), factories.a_moment_after(open_ticket.updated_at)
			)
