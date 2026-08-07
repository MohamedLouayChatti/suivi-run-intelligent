from __future__ import annotations

from app.modules.analytics.application.dto.attention_required_dto import AttentionRequiredDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.queries.get_attention_required.query import GetAttentionRequiredQuery
from app.modules.analytics.application.queries.user_enricher import AnalyticsUserEnricher
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class GetAttentionRequiredHandler:
	def __init__(self, repository: AnalyticsReadRepository, user_repository: UserReadRepository) -> None:
		self.repository = repository
		self.enricher = AnalyticsUserEnricher(user_repository)

	async def handle(self, query: GetAttentionRequiredQuery) -> AttentionRequiredDTO:
		data = await self.repository.get_attention_required(query.applications, query.threshold_days)
		return await self.enricher.attention_required(data)
