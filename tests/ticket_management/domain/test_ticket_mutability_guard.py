"""
`Ticket._ensure_mutable()` (closed + archived guard) is applied consistently
by assign, reassign, mark_pending, resume, resolve, close, change_priority,
add_comment, add_attachment, edit_comment, delete_comment,
add_attachment_to_comment, delete_attachment_from_comment and
transfer_application.

`start_progress` is the one exception: it calls `_transition_to` directly
without going through `_ensure_mutable`, so it only blocks CLOSED tickets
(via the redundant check inside `_transition_to`) and does NOT block
ARCHIVED tickets. This test file documents that current behavior exactly
as implemented. See the accompanying report for why this is flagged as a
design inconsistency rather than silently relied upon.
"""
from __future__ import annotations

from app.modules.ticket_management.domain.enums.status import Status
from tests.ticket_management.domain import factories


class TestStartProgressArchivedInconsistency:
	def test_start_progress_on_an_archived_ticket_currently_succeeds(self, archived_ticket):
		# NOTE: every other mutator (assign, change_priority, add_comment,
		# etc.) raises TicketArchived here. start_progress does not, because
		# it bypasses `_ensure_mutable`. This test pins the *current*
		# behavior; if this is fixed, this test should be updated to expect
		# TicketArchived instead, alongside the other guarded methods.
		moment = factories.a_moment_after(archived_ticket.updated_at)

		archived_ticket.start_progress(moment)

		assert archived_ticket.status == Status.IN_PROGRESS
