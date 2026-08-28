from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.analytics.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority


@dataclass(frozen=True)
class ResolvedTicketDurationDTO:
	"""One resolved ticket and how long it took, for the "which ones took longest" ranking.

	`resolution_hours` is `resolved_at - created_at`, the same duration every average in this
	module is computed from -- so a ticket named here and the mean it contributed to are always
	measuring the same thing.
	"""

	ticket_id: UUID
	title: str
	application: Application
	priority: Priority
	created_at: datetime
	resolved_at: datetime
	resolution_hours: float
	assignee_id: UUID
	assignee: UserSummaryDTO | None = None


@dataclass(frozen=True)
class ResolutionRankingDTO:
	"""`total_resolved` is every ticket the filters matched, not just the ranked few: a "slowest
	ticket" only means something against how many were in the running."""

	total_resolved: int
	slowest_first: bool
	tickets: list[ResolvedTicketDurationDTO]
