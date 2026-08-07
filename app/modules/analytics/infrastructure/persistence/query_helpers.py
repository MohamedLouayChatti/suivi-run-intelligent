from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TypeVar
from uuid import UUID

from sqlalchemy import ColumnElement, Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
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


def assignee_filter(assignee_id: UUID) -> ColumnElement[bool]:
	return TicketModel.assignee_id == assignee_id


async def bucketed_activity_trend(
	session: AsyncSession, *, extra_condition: ColumnElement[bool] | None, bucket_count: int, span_days: int
) -> list[ActivityPointDTO]:
	"""Shared bucketing logic behind both the application-scoped and the per-assignee
	("my activity") activity trends -- same two grouped-count queries (by created_at,
	by resolved_at), just filtered differently by the caller."""
	now = datetime.now(UTC)
	origin = now - timedelta(days=bucket_count * span_days)
	span_seconds = span_days * 86400

	def bucket_index(column):
		return func.floor(func.extract("epoch", column - origin) / span_seconds)

	created_stmt = select(bucket_index(TicketModel.created_at).label("bucket"), func.count().label("count")).where(
		TicketModel.created_at >= origin, TicketModel.created_at <= now, not_archived()
	)
	resolved_stmt = select(bucket_index(TicketModel.resolved_at).label("bucket"), func.count().label("count")).where(
		TicketModel.resolved_at.is_not(None), TicketModel.resolved_at >= origin, TicketModel.resolved_at <= now, not_archived()
	)
	if extra_condition is not None:
		created_stmt = created_stmt.where(extra_condition)
		resolved_stmt = resolved_stmt.where(extra_condition)
	created_stmt = created_stmt.group_by("bucket")
	resolved_stmt = resolved_stmt.group_by("bucket")

	created_by_bucket = {int(r.bucket): r.count for r in (await session.execute(created_stmt)).all()}
	resolved_by_bucket = {int(r.bucket): r.count for r in (await session.execute(resolved_stmt)).all()}

	return [
		ActivityPointDTO(
			bucket_start=origin + timedelta(days=index * span_days),
			created=created_by_bucket.get(index, 0),
			resolved=resolved_by_bucket.get(index, 0),
		)
		for index in range(bucket_count)
	]


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
