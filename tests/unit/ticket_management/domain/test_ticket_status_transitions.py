"""
Tests for the ticket status state machine.

Allowed transitions, per `Ticket._transition_to`:
	OPEN        -> IN_PROGRESS
	IN_PROGRESS -> PENDING, RESOLVED
	PENDING     -> IN_PROGRESS
	RESOLVED    -> IN_PROGRESS, CLOSED
	CLOSED      -> (terminal)

These tests exercise the public transition methods (start_progress,
mark_pending, resume, resolve, close) rather than the private
`_transition_to` helper, since the state machine's contract is what
matters, not how it is implemented internally.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.exceptions import (
	InvalidStatusTransition,
	PendingReasonRequired,
	ResolutionNotesRequired,
	TicketClosed,
)
from tests.unit.ticket_management.domain import factories


class TestStartProgress:
	def test_open_ticket_moves_to_in_progress(self, open_ticket):
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.start_progress(moment)

		assert open_ticket.status == Status.IN_PROGRESS
		assert open_ticket.updated_at == moment

	def test_closed_ticket_cannot_restart(self, closed_ticket):
		with pytest.raises(TicketClosed):
			closed_ticket.start_progress(factories.a_moment_after(closed_ticket.updated_at))


class TestMarkPending:
	def test_in_progress_ticket_can_be_marked_pending(self, in_progress_ticket):
		moment = factories.a_moment_after(in_progress_ticket.updated_at)

		in_progress_ticket.mark_pending("Waiting on vendor", moment)

		assert in_progress_ticket.status == Status.PENDING
		assert in_progress_ticket.pending_reason == "Waiting on vendor"
		assert in_progress_ticket.updated_at == moment

	@pytest.mark.parametrize("blank_reason", ["", "   "])
	def test_requires_a_non_blank_reason(self, in_progress_ticket, blank_reason):
		with pytest.raises(PendingReasonRequired):
			in_progress_ticket.mark_pending(blank_reason, factories.a_moment_after(in_progress_ticket.updated_at))

	def test_open_ticket_cannot_go_directly_to_pending(self, open_ticket):
		with pytest.raises(InvalidStatusTransition):
			open_ticket.mark_pending("reason", factories.a_moment_after(open_ticket.updated_at))


class TestResume:
	def test_pending_ticket_resumes_to_in_progress_and_clears_reason(self, pending_ticket):
		moment = factories.a_moment_after(pending_ticket.updated_at)

		pending_ticket.resume(moment)

		assert pending_ticket.status == Status.IN_PROGRESS
		assert pending_ticket.pending_reason is None
		assert pending_ticket.updated_at == moment

	def test_resolved_ticket_resumes_to_in_progress_and_clears_resolution(self, resolved_ticket):
		moment = factories.a_moment_after(resolved_ticket.updated_at)

		resolved_ticket.resume(moment)

		assert resolved_ticket.status == Status.IN_PROGRESS
		assert resolved_ticket.resolved_at is None
		assert resolved_ticket.resolution_notes is None

	def test_open_ticket_cannot_resume(self, open_ticket):
		with pytest.raises(InvalidStatusTransition):
			open_ticket.resume(factories.a_moment_after(open_ticket.updated_at))

	def test_in_progress_ticket_cannot_resume(self, in_progress_ticket):
		with pytest.raises(InvalidStatusTransition):
			in_progress_ticket.resume(factories.a_moment_after(in_progress_ticket.updated_at))


class TestResolve:
	def test_in_progress_ticket_can_be_resolved(self, in_progress_ticket):
		moment = factories.a_moment_after(in_progress_ticket.updated_at)

		in_progress_ticket.resolve("Fixed by restarting the worker", moment)

		assert in_progress_ticket.status == Status.RESOLVED
		assert in_progress_ticket.resolution_notes == "Fixed by restarting the worker"
		assert in_progress_ticket.resolved_at == moment

	def test_resolving_clears_any_pending_reason(self, in_progress_ticket):
		# Regression guard: resolve() must clear a stale pending_reason even
		# though a ticket must pass through IN_PROGRESS (via resume) to get
		# here, since pending_reason is not otherwise cleared by resume().
		in_progress_ticket.mark_pending("waiting", factories.a_moment_after(in_progress_ticket.updated_at))
		in_progress_ticket.resume(factories.a_moment_after(in_progress_ticket.updated_at))

		in_progress_ticket.resolve("Fixed", factories.a_moment_after(in_progress_ticket.updated_at))

		assert in_progress_ticket.pending_reason is None

	@pytest.mark.parametrize("blank_notes", ["", "   "])
	def test_requires_non_blank_resolution_notes(self, in_progress_ticket, blank_notes):
		with pytest.raises(ResolutionNotesRequired):
			in_progress_ticket.resolve(blank_notes, factories.a_moment_after(in_progress_ticket.updated_at))

	def test_pending_ticket_cannot_be_resolved_directly(self, pending_ticket):
		# Must resume() back to IN_PROGRESS first; PENDING -> RESOLVED is not
		# an allowed direct transition.
		with pytest.raises(InvalidStatusTransition):
			pending_ticket.resolve("Fixed", factories.a_moment_after(pending_ticket.updated_at))


class TestClose:
	def test_resolved_ticket_can_be_closed(self, resolved_ticket):
		moment = factories.a_moment_after(resolved_ticket.updated_at)

		resolved_ticket.close(moment)

		assert resolved_ticket.status == Status.CLOSED
		assert resolved_ticket.closed_at == moment

	def test_open_ticket_cannot_be_closed_directly(self, open_ticket):
		with pytest.raises(InvalidStatusTransition):
			open_ticket.close(factories.a_moment_after(open_ticket.updated_at))

	def test_already_closed_ticket_cannot_be_closed_again(self, closed_ticket):
		with pytest.raises(TicketClosed):
			closed_ticket.close(factories.a_moment_after(closed_ticket.updated_at))
