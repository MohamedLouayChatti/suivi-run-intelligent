"""
Plain factory functions for building domain entities with sensible defaults.

These are intentionally *not* pytest fixtures: fixtures are for wiring
(dependency injection into test functions), factories are for data
construction. Keeping them as plain functions lets both the domain tests
and the application tests (via fakes) reuse the exact same construction
logic without needing to depend on pytest's fixture graph.

Every factory accepts keyword overrides so individual tests can tweak only
the field they care about while keeping the rest at safe defaults.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status

BASE_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def a_moment_after(moment: datetime, minutes: int = 1) -> datetime:
	"""Returns a deterministic, strictly-later timestamp for sequencing events in tests."""
	return moment + timedelta(minutes=minutes)


def new_uuid() -> UUID:
	return uuid4()


def make_ticket(
	*,
	id: UUID | None = None,
	title: str = "Payment gateway returns 500",
	description: str = "Customers report failed checkouts since the last deploy.",
	priority: Priority = Priority.MEDIUM,
	application: Application = Application.APP_1,
	created_at: datetime = BASE_TIME,
	assignee_id: UUID | None = None,
) -> Ticket:
	"""Builds a freshly created (OPEN, unassigned unless specified) ticket."""
	return Ticket.create(
		id=id or new_uuid(),
		title=title,
		description=description,
		priority=priority,
		created_at=created_at,
		application=application,
		assignee_id=assignee_id,
	)


def make_assigned_ticket(*, assignee_id: UUID | None = None, **overrides) -> Ticket:
	"""An OPEN ticket that already has an assignee."""
	ticket = make_ticket(**overrides)
	ticket.assign(assignee_id or new_uuid(), a_moment_after(ticket.created_at))
	return ticket


def make_in_progress_ticket(**overrides) -> Ticket:
	ticket = make_ticket(**overrides)
	ticket.start_progress(a_moment_after(ticket.created_at))
	return ticket


def make_pending_ticket(*, reason: str = "Waiting on customer logs", **overrides) -> Ticket:
	ticket = make_in_progress_ticket(**overrides)
	ticket.mark_pending(reason, a_moment_after(ticket.updated_at))
	return ticket


def make_resolved_ticket(*, notes: str = "Rolled back the faulty deploy.", **overrides) -> Ticket:
	ticket = make_in_progress_ticket(**overrides)
	ticket.resolve(notes, a_moment_after(ticket.updated_at))
	return ticket


def make_closed_ticket(**overrides) -> Ticket:
	ticket = make_resolved_ticket(**overrides)
	ticket.close(a_moment_after(ticket.updated_at))
	return ticket


def make_archived_ticket(**overrides) -> Ticket:
	ticket = make_ticket(**overrides)
	ticket.archive(a_moment_after(ticket.created_at))
	return ticket


def make_comment(
	*,
	id: UUID | None = None,
	author_id: UUID | None = None,
	content: str = "Looks like the timeout is on the payment provider's side.",
	created_at: datetime = BASE_TIME,
) -> Comment:
	return Comment.create(
		id=id or new_uuid(),
		author_id=author_id or new_uuid(),
		content=content,
		created_at=created_at,
	)


def make_attachment(
	*,
	id: UUID | None = None,
	filename: str = "stack-trace.log",
	content_type: str = "text/plain",
	storage_path: str = "s3://tickets/attachments/stack-trace.log",
	uploaded_by: UUID | None = None,
	uploaded_at: datetime = BASE_TIME,
) -> Attachment:
	return Attachment.create(
		id=id or new_uuid(),
		filename=filename,
		content_type=content_type,
		storage_path=storage_path,
		uploaded_by=uploaded_by or new_uuid(),
		uploaded_at=uploaded_at,
	)
