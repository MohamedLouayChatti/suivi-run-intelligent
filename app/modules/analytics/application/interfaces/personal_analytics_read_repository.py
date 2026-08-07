from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
from app.modules.analytics.application.dto.my_kpi_snapshot_dto import MyKpiSnapshotDTO
from app.modules.analytics.application.support.time_range import DateWindow


class PersonalAnalyticsReadRepository(ABC):
	"""Backs the Dashboard's "my" widgets -- scoped to a single assignee (the caller),
	never to an application: an assignee's own tickets are visible to them regardless of
	their current application assignments (same "assignee always sees their own ticket"
	precedent as TicketAccessPolicy's assignee-only operations)."""

	@abstractmethod
	async def get_my_kpi_totals(self, assignee_id: UUID, window: DateWindow) -> MyKpiSnapshotDTO:
		raise NotImplementedError

	@abstractmethod
	async def get_my_activity_trend(self, assignee_id: UUID) -> list[ActivityPointDTO]:
		"""Always the trailing 30 days, one point per day -- matches the Dashboard's
		fixed "30 derniers jours" chart (no time-range selector on that page)."""
		raise NotImplementedError
