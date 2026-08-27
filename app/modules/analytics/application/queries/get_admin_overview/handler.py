from __future__ import annotations

from app.modules.analytics.application.dto.admin_overview_dto import AdminOverviewDTO, ApplicationHealthDTO
from app.modules.analytics.application.interfaces.admin_analytics_read_repository import AdminAnalyticsReadRepository
from app.modules.analytics.application.queries.get_admin_overview.query import GetAdminOverviewQuery
from app.modules.analytics.application.queries.user_enricher import AnalyticsUserEnricher
from app.modules.analytics.application.support.time_range import resolve_window
from app.modules.analytics.domain.repositories.health_baseline_repository import HealthBaselineRepository
from app.modules.analytics.domain.services import health_tiering
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class GetAdminOverviewHandler:
	def __init__(
		self, repository: AdminAnalyticsReadRepository, user_repository: UserReadRepository,
		health_baselines: HealthBaselineRepository,
	) -> None:
		self.repository = repository
		self.enricher = AnalyticsUserEnricher(user_repository)
		self.health_baselines = health_baselines

	async def handle(self, query: GetAdminOverviewQuery) -> AdminOverviewDTO:
		window = resolve_window(query.time_range).current
		team = await self.enricher.team_overview(await self.repository.get_team_overview(window))
		signals = await self.repository.get_health(window)
		baselines = await self.health_baselines.get_all()
		health = [
			ApplicationHealthDTO(
				application=signal.application,
				health=health_tiering.combined_tier(
					signal.active_tickets, signal.avg_resolution_hours, baselines.get(signal.application)
				),
				active_tickets=signal.active_tickets,
				avg_resolution_hours=signal.avg_resolution_hours,
				urgent_tickets=signal.urgent_tickets,
			)
			for signal in signals
		]
		return AdminOverviewDTO(
			workload=await self.repository.get_workload(window),
			health=health,
			resolution_time=await self.repository.get_resolution_time_comparison(window),
			jira_dependency=await self.repository.get_jira_dependency(window),
			transfer_rate=await self.repository.get_transfer_rate(window),
			monthly_trends=await self.repository.get_monthly_trends(),
			team=team,
		)
