from __future__ import annotations

from app.modules.analytics.application.dto.jira_metrics_dto import JiraMetricsDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.queries.get_jira_metrics.query import GetJiraMetricsQuery
from app.modules.analytics.application.support.time_range import resolve_window


class GetJiraMetricsHandler:
	def __init__(self, repository: AnalyticsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetJiraMetricsQuery) -> JiraMetricsDTO:
		window = resolve_window(query.time_range).current
		return await self.repository.get_jira_metrics(query.applications, window)
