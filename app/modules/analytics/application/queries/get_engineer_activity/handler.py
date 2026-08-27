from __future__ import annotations

from dataclasses import replace

from app.modules.analytics.application.dto.engineer_activity_dto import EngineerActivityDTO
from app.modules.analytics.application.interfaces.engineer_activity_read_repository import (
	EngineerActivityReadRepository,
)
from app.modules.analytics.application.queries.get_engineer_activity.query import GetEngineerActivityQuery
from app.modules.analytics.application.queries.user_enricher import AnalyticsUserEnricher
from app.modules.analytics.application.support.time_range import resolve_window
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class GetEngineerActivityHandler:
	def __init__(self, repository: EngineerActivityReadRepository, user_repository: UserReadRepository) -> None:
		self.repository = repository
		self.enricher = AnalyticsUserEnricher(user_repository)

	async def handle(self, query: GetEngineerActivityQuery) -> EngineerActivityDTO:
		window = resolve_window(query.time_range).current
		activity = await self.repository.get_engineer_activity(query.engineer_id, query.applications, window)
		return replace(activity, engineer=await self.enricher.engineer(query.engineer_id))
