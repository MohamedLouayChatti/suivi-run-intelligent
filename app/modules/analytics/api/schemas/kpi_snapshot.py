from __future__ import annotations

from pydantic import BaseModel

from app.modules.analytics.application.dto.kpi_snapshot_dto import KpiSnapshotDTO, KpiTrendsDTO


class KpiTrendsResponse(BaseModel):
	total_tickets: float
	open_tickets: float
	resolved_tickets: float
	avg_resolution_hours: float
	urgent_tickets: float

	@classmethod
	def from_dto(cls, trends: KpiTrendsDTO) -> KpiTrendsResponse:
		return cls(
			total_tickets=trends.total_tickets,
			open_tickets=trends.open_tickets,
			resolved_tickets=trends.resolved_tickets,
			avg_resolution_hours=trends.avg_resolution_hours,
			urgent_tickets=trends.urgent_tickets,
		)


class KpiSnapshotResponse(BaseModel):
	total_tickets: int
	open_tickets: int
	resolved_tickets: int
	avg_resolution_hours: float
	urgent_tickets: int
	trends: KpiTrendsResponse

	@classmethod
	def from_dto(cls, snapshot: KpiSnapshotDTO) -> KpiSnapshotResponse:
		return cls(
			total_tickets=snapshot.total_tickets,
			open_tickets=snapshot.open_tickets,
			resolved_tickets=snapshot.resolved_tickets,
			avg_resolution_hours=snapshot.avg_resolution_hours,
			urgent_tickets=snapshot.urgent_tickets,
			trends=KpiTrendsResponse.from_dto(snapshot.trends),
		)
