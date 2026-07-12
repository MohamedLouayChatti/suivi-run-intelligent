from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import CommentDeleted, DuplicateAttachment, EmptyComment
from tests.unit.ticket_management.domain import factories


class TestCommentCreation:
	@pytest.mark.parametrize("blank_content", ["", "   ", "\n"])
	def test_rejects_blank_content(self, blank_content):
		with pytest.raises(EmptyComment):
			factories.make_comment(content=blank_content)

	def test_new_comment_is_not_deleted_or_edited(self, comment):
		assert comment.deleted_at is None
		assert comment.edited_at is None


class TestCommentEdit:
	def test_edits_content_and_stamps_edited_at(self, comment):
		moment = factories.a_moment_after(comment.created_at)

		comment.edit("Updated diagnosis", moment)

		assert comment.content == "Updated diagnosis"
		assert comment.edited_at == moment

	@pytest.mark.parametrize("blank_content", ["", "   "])
	def test_rejects_blank_content(self, comment, blank_content):
		with pytest.raises(EmptyComment):
			comment.edit(blank_content, factories.a_moment_after(comment.created_at))

	def test_cannot_edit_a_deleted_comment(self, comment):
		comment.delete(factories.a_moment_after(comment.created_at))

		with pytest.raises(CommentDeleted):
			comment.edit("New content", factories.a_moment_after(comment.created_at))


class TestCommentDelete:
	def test_deletes_a_comment(self, comment):
		moment = factories.a_moment_after(comment.created_at)

		comment.delete(moment)

		assert comment.deleted_at == moment

	def test_cannot_delete_an_already_deleted_comment(self, comment):
		comment.delete(factories.a_moment_after(comment.created_at))

		with pytest.raises(CommentDeleted):
			comment.delete(factories.a_moment_after(comment.created_at))


class TestCommentAttachments:
	def test_adds_an_attachment_and_stamps_edited_at(self, comment, attachment):
		moment = factories.a_moment_after(comment.created_at)

		comment.add_attachment(attachment, moment)

		assert attachment in comment.attachments
		assert comment.edited_at == moment

	def test_cannot_add_the_same_attachment_twice(self, comment, attachment):
		comment.add_attachment(attachment, factories.a_moment_after(comment.created_at))

		with pytest.raises(DuplicateAttachment):
			comment.add_attachment(attachment, factories.a_moment_after(comment.created_at))

	def test_cannot_add_an_attachment_to_a_deleted_comment(self, comment, attachment):
		comment.delete(factories.a_moment_after(comment.created_at))

		with pytest.raises(CommentDeleted):
			comment.add_attachment(attachment, factories.a_moment_after(comment.created_at))
