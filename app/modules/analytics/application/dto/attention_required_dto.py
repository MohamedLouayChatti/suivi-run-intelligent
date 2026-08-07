from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.analytics.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.ticket_management.domain.enums.priority import Priority


@dataclass(frozen=True)
class AgingIncidentDTO:
	ticket_id: UUID
	title: str
	age_days: int
	priority: Priority
	assignee_id: UUID
	assignee: UserSummaryDTO | None = None


@dataclass(frozen=True)
class AttentionRequiredDTO:
	"""Live snapshot, not time-windowed: tickets currently OPEN/IN_PROGRESS whose age
	(now - created_at) exceeds threshold_days. `count` may exceed len(incidents) -- only
	the oldest `incidents` are returned in full."""

	count: int
	threshold_days: int
	incidents: list[AgingIncidentDTO]
