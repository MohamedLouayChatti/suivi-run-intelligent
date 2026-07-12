from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.change_status.command import ChangeStatusCommand
from app.modules.ticket_management.application.commands.change_status.handler import ChangeStatusHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.modules.ticket_management.domain.exceptions import InvalidStatusTransition, PendingReasonRequired
from tests.unit.ticket_management.domain import factories


class TestChangeStatusHandler:
	@pytest.mark.asyncio
	async def test_moves_an_open_ticket_to_in_progress(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ChangeStatusHandler(uow, event_publisher)

		await handler.handle(ChangeStatusCommand(ticket_id=ticket.id, status=Status.IN_PROGRESS, changed_at=moment))

		assert ticket.status == Status.IN_PROGRESS
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_marks_an_in_progress_ticket_pending_with_the_given_reason(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_in_progress_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ChangeStatusHandler(uow, event_publisher)

		await handler.handle(
			ChangeStatusCommand(ticket_id=ticket.id, status=Status.PENDING, changed_at=moment, pending_reason="Waiting on customer")
		)

		assert ticket.status == Status.PENDING
		assert ticket.pending_reason == "Waiting on customer"

	@pytest.mark.asyncio
	async def test_pending_without_a_reason_raises(self, uow, event_publisher, ticket_repository):
		# The handler defaults a missing pending_reason to "", which the
		# domain then rejects as blank.
		ticket = ticket_repository.seed(factories.make_in_progress_ticket())
		handler = ChangeStatusHandler(uow, event_publisher)

		with pytest.raises(PendingReasonRequired):
			await handler.handle(
				ChangeStatusCommand(ticket_id=ticket.id, status=Status.PENDING, changed_at=factories.a_moment_after(ticket.updated_at))
			)

	@pytest.mark.asyncio
	async def test_resolves_an_in_progress_ticket_with_notes(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_in_progress_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ChangeStatusHandler(uow, event_publisher)

		await handler.handle(
			ChangeStatusCommand(ticket_id=ticket.id, status=Status.RESOLVED, changed_at=moment, resolution_notes="Fixed the config")
		)

		assert ticket.status == Status.RESOLVED
		assert ticket.resolution_notes == "Fixed the config"

	@pytest.mark.asyncio
	async def test_closes_a_resolved_ticket(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_resolved_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ChangeStatusHandler(uow, event_publisher)

		await handler.handle(ChangeStatusCommand(ticket_id=ticket.id, status=Status.CLOSED, changed_at=moment))

		assert ticket.status == Status.CLOSED

	@pytest.mark.asyncio
	async def test_publishes_ticket_status_changed_with_old_and_new_status(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ChangeStatusHandler(uow, event_publisher)

		await handler.handle(ChangeStatusCommand(ticket_id=ticket.id, status=Status.IN_PROGRESS, changed_at=moment))

		assert event_publisher.last == TicketStatusChanged(
			ticket_id=ticket.id, old_status=Status.OPEN, new_status=Status.IN_PROGRESS, changed_at=moment
		)

	@pytest.mark.asyncio
	async def test_an_unsupported_target_status_raises_value_error(self, uow, event_publisher, ticket_repository):
		# OPEN is a valid Status value but is not a status the handler's
		# if/elif chain knows how to transition *to* (there is no
		# "reopen"/"OPEN" branch), so it falls through to the explicit
		# ValueError guard.
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = ChangeStatusHandler(uow, event_publisher)

		with pytest.raises(ValueError, match="Unsupported status transition"):
			await handler.handle(ChangeStatusCommand(ticket_id=ticket.id, status=Status.OPEN, changed_at=factories.a_moment_after(ticket.updated_at)))

		assert uow.committed is False
		assert event_publisher.published == []

	@pytest.mark.asyncio
	async def test_invalid_transition_propagates_without_committing(self, uow, event_publisher, ticket_repository):
		# OPEN -> RESOLVED is not an allowed direct transition (must pass
		# through IN_PROGRESS first). Resolution notes are supplied so the
		# transition check itself is what's under test here, rather than the
		# earlier "notes required" guard.
		ticket = ticket_repository.seed(factories.make_ticket())  # OPEN
		handler = ChangeStatusHandler(uow, event_publisher)

		with pytest.raises(InvalidStatusTransition):
			await handler.handle(
				ChangeStatusCommand(
					ticket_id=ticket.id,
					status=Status.RESOLVED,
					changed_at=factories.a_moment_after(ticket.updated_at),
					resolution_notes="Fixed",
				)
			)

		assert uow.committed is False
		assert event_publisher.published == []

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = ChangeStatusHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(ChangeStatusCommand(ticket_id=factories.new_uuid(), status=Status.IN_PROGRESS, changed_at=factories.BASE_TIME))
