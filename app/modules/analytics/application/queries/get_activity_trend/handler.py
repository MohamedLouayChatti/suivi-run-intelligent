from __future__ import annotations

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.queries.get_activity_trend.query import GetActivityTrendQuery


class GetActivityTrendHandler:
	def __init__(self, repository: AnalyticsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetActivityTrendQuery) -> list[ActivityPointDTO]:
		return await self.repository.get_activity_trend(query.applications, query.time_range)
