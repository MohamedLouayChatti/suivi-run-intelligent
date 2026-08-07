from __future__ import annotations

from app.modules.analytics.application.dto.kpi_snapshot_dto import KpiSnapshotDTO, KpiTrendsDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.queries.get_kpi_snapshot.query import GetKpiSnapshotQuery
from app.modules.analytics.application.support.time_range import resolve_window, trend_pct


class GetKpiSnapshotHandler:
	def __init__(self, repository: AnalyticsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetKpiSnapshotQuery) -> KpiSnapshotDTO:
		window = resolve_window(query.time_range)
		current = await self.repository.get_kpi_totals(query.applications, window.current)
		previous = await self.repository.get_kpi_totals(query.applications, window.previous)
		trends = KpiTrendsDTO(
			total_tickets=trend_pct(current.total_tickets, previous.total_tickets),
			open_tickets=trend_pct(current.open_tickets, previous.open_tickets),
			resolved_tickets=trend_pct(current.resolved_tickets, previous.resolved_tickets),
			avg_resolution_hours=trend_pct(current.avg_resolution_hours, previous.avg_resolution_hours),
			urgent_tickets=trend_pct(current.urgent_tickets, previous.urgent_tickets),
		)
		return KpiSnapshotDTO(
			total_tickets=current.total_tickets,
			open_tickets=current.open_tickets,
			resolved_tickets=current.resolved_tickets,
			avg_resolution_hours=current.avg_resolution_hours,
			urgent_tickets=current.urgent_tickets,
			trends=trends,
		)
