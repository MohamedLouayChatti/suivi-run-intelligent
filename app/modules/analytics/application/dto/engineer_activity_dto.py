from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.analytics.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class EngineerActivityDTO:
	"""One engineer's own workload profile: what they are carrying now, what they closed over
	the window, and what kind of work it is.

	Same event-based time semantics as the rest of this module: `created_tickets`,
	`by_application`, `by_category`, `by_status` and `transfer_rate_pct` all describe the
	created-in-window cohort grouped by its *current* attributes, `resolved_tickets` and
	`avg_resolution_hours` describe resolutions that happened in the window whenever the ticket
	was opened, and `active_tickets` is a live count with no window at all -- the same
	point-in-time reading TeamOverviewDTO's own active count takes.
	"""

	engineer_id: UUID
	active_tickets: int
	created_tickets: int
	resolved_tickets: int
	avg_resolution_hours: float
	transfer_rate_pct: float
	by_application: dict[Application, int]
	by_category: dict[Category, int]
	by_status: dict[Status, int]
	engineer: UserSummaryDTO | None = None
