"""
`Ticket._ensure_mutable()` (closed + archived guard) is applied consistently
by assign, reassign, mark_pending, resume, resolve, close, change_priority,
add_comment, add_attachment, edit_comment, delete_comment,
add_attachment_to_comment, delete_attachment_from_comment,
transfer_application, and start_progress.
"""
from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import TicketArchived
from tests.unit.ticket_management.domain import factories


class TestStartProgressArchivedGuard:
	def test_start_progress_on_an_archived_ticket_raises_ticket_archived(self, archived_ticket):
		moment = factories.a_moment_after(archived_ticket.updated_at)

		with pytest.raises(TicketArchived):
			archived_ticket.start_progress(moment)
