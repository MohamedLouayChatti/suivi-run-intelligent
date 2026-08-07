from __future__ import annotations

from app.modules.analytics.application.dto.distributions_dto import DistributionsDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.queries.get_distributions.query import GetDistributionsQuery
from app.modules.analytics.application.support.time_range import resolve_window


class GetDistributionsHandler:
	def __init__(self, repository: AnalyticsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetDistributionsQuery) -> DistributionsDTO:
		window = resolve_window(query.time_range).current
		return await self.repository.get_distributions(query.applications, window)
