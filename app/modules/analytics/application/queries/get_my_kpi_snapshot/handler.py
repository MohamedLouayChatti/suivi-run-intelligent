from __future__ import annotations

from app.modules.analytics.application.dto.my_kpi_snapshot_dto import MyKpiSnapshotDTO
from app.modules.analytics.application.interfaces.personal_analytics_read_repository import (
	PersonalAnalyticsReadRepository,
)
from app.modules.analytics.application.queries.get_my_kpi_snapshot.query import (
	PERSONAL_KPI_WINDOW_DAYS, GetMyKpiSnapshotQuery,
)
from app.modules.analytics.application.support.time_range import window_for_days


class GetMyKpiSnapshotHandler:
	def __init__(self, repository: PersonalAnalyticsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetMyKpiSnapshotQuery) -> MyKpiSnapshotDTO:
		window = window_for_days(PERSONAL_KPI_WINDOW_DAYS)
		return await self.repository.get_my_kpi_totals(query.assignee_id, window)
