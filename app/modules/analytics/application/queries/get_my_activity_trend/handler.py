from __future__ import annotations

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
from app.modules.analytics.application.interfaces.personal_analytics_read_repository import (
	PersonalAnalyticsReadRepository,
)
from app.modules.analytics.application.queries.get_my_activity_trend.query import GetMyActivityTrendQuery


class GetMyActivityTrendHandler:
	def __init__(self, repository: PersonalAnalyticsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetMyActivityTrendQuery) -> list[ActivityPointDTO]:
		return await self.repository.get_my_activity_trend(query.assignee_id)
