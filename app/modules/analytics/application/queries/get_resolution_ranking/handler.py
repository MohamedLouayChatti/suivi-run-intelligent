from __future__ import annotations

from dataclasses import replace

from app.modules.analytics.application.dto.resolution_ranking_dto import ResolutionRankingDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.queries.get_resolution_ranking.query import (
	MAX_RANKED_TICKETS,
	GetResolutionRankingQuery,
)
from app.modules.analytics.application.queries.user_enricher import AnalyticsUserEnricher
from app.modules.analytics.application.support.time_range import resolve_window
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class GetResolutionRankingHandler:
	def __init__(self, repository: AnalyticsReadRepository, user_repository: UserReadRepository) -> None:
		self.repository = repository
		self.enricher = AnalyticsUserEnricher(user_repository)

	async def handle(self, query: GetResolutionRankingQuery) -> ResolutionRankingDTO:
		window = None if query.time_range is None else resolve_window(query.time_range).current
		ranking = await self.repository.get_resolution_ranking(
			applications=query.applications,
			window=window,
			assignee_id=query.assignee_id,
			slowest_first=query.slowest_first,
			limit=min(query.limit, MAX_RANKED_TICKETS),
		)
		users = await self.enricher.assignees({ticket.assignee_id for ticket in ranking.tickets})
		return replace(
			ranking,
			tickets=[replace(ticket, assignee=users.get(ticket.assignee_id)) for ticket in ranking.tickets],
		)
