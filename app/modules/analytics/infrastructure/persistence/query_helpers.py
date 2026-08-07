from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from typing import TypeVar

from sqlalchemy import ColumnElement, Select, and_, func, select

from app.modules.analytics.application.support.time_range import DateWindow
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType
from app.modules.ticket_management.infrastructure.persistence.models.ticket_history_model import TicketHistoryModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel

ACTIVE_STATUSES = (Status.OPEN, Status.IN_PROGRESS)

# Resolution duration in hours, for tickets that have been resolved (resolved_at set).
DURATION_HOURS = func.extract("epoch", TicketModel.resolved_at - TicketModel.created_at) / 3600.0


def not_archived() -> ColumnElement[bool]:
	return TicketModel.archived_at.is_(None)


def created_in(window: DateWindow) -> ColumnElement[bool]:
	"""The "created in period" cohort -- the basis for every count/grouping that has no
	dedicated event date of its own (totals, open/urgent counts, distributions)."""
	return and_(TicketModel.created_at >= window.start, TicketModel.created_at <= window.end, not_archived())


def resolved_in(window: DateWindow) -> ColumnElement[bool]:
	"""Tickets whose resolution *happened* within the period, regardless of when they
	were created -- the event-based basis for every "resolved"/avg-resolution metric."""
	return and_(
		TicketModel.resolved_at.is_not(None),
		TicketModel.resolved_at >= window.start,
		TicketModel.resolved_at <= window.end,
		not_archived(),
	)


def application_filter(applications: frozenset[Application] | None) -> ColumnElement[bool] | None:
	if applications is None:
		return None
	return TicketModel.application.in_(applications)


def ever_transferred() -> ColumnElement[bool]:
	"""True when a ticket has at least one TRANSFERRED history entry.

	`tickets.transferred_to` is NOT a reliable "was ever transferred" signal -- it gets
	nulled out by Ticket.resume() when a TRANSFERRED ticket resumes progress. The
	append-only ticket_history table is the actual source of truth.
	"""
	transferred_ids: Select = select(TicketHistoryModel.ticket_id).where(
		TicketHistoryModel.event_type == TicketHistoryEventType.TRANSFERRED
	)
	return TicketModel.id.in_(transferred_ids)


EnumT = TypeVar("EnumT", bound=Enum)


def full_counts(enum_cls: type[EnumT], rows: Iterable[tuple[EnumT, int]]) -> dict[EnumT, int]:
	"""Every enum member present, defaulting to 0, overlaid with the grouped counts
	actually returned by the database (members with no matching rows are simply absent
	from `rows`)."""
	counts = dict.fromkeys(enum_cls, 0)
	counts.update(dict(rows))
	return counts
