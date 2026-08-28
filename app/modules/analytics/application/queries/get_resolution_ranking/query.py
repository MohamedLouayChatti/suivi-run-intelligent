from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.ticket_management.domain.enums.application import Application

MAX_RANKED_TICKETS = 20


@dataclass(frozen=True)
class GetResolutionRankingQuery:
	"""Rank resolved tickets by how long they took.

	`time_range` is optional here, unlike every other query in this module: "which ticket took
	longest" is naturally asked of the whole history, and forcing a window would answer a
	narrower question than the one put. When it is set, the window is applied to `resolved_at`
	-- the same event-based semantics every other resolution metric uses.
	"""

	applications: frozenset[Application] | None = None
	assignee_id: UUID | None = None
	time_range: TimeRange | None = None
	slowest_first: bool = True
	limit: int = 5
