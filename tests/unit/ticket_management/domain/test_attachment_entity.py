from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import AttachmentDeleted, TicketDomainError
from tests.unit.ticket_management.domain import factories


class TestAttachmentCreation:
	def test_creates_an_attachment_that_is_not_deleted(self, attachment):
		assert attachment.deleted_at is None

	@pytest.mark.parametrize(
		"factory",
		[
			lambda: factories.make_attachment(filename=" "),
			lambda: factories.make_attachment(content_type=" "),
			lambda: factories.make_attachment(storage_path=" "),
		],
	)
	def test_rejects_blank_required_metadata(self, factory):
		with pytest.raises(TicketDomainError):
			factory()


class TestAttachmentDelete:
	def test_deletes_an_attachment(self, attachment):
		moment = factories.a_moment_after(attachment.uploaded_at)

		attachment.delete(moment)

		assert attachment.deleted_at == moment

	def test_cannot_delete_an_already_deleted_attachment(self, attachment):
		attachment.delete(factories.a_moment_after(attachment.uploaded_at))

		with pytest.raises(AttachmentDeleted):
			attachment.delete(factories.a_moment_after(attachment.uploaded_at))
