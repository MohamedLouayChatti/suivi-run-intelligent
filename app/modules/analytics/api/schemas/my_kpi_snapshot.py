from __future__ import annotations

from pydantic import BaseModel

from app.modules.analytics.application.dto.my_kpi_snapshot_dto import MyKpiSnapshotDTO


class MyKpiSnapshotResponse(BaseModel):
	resolved_this_week: int
	created_this_week: int
	avg_resolution_hours: float

	@classmethod
	def from_dto(cls, snapshot: MyKpiSnapshotDTO) -> MyKpiSnapshotResponse:
		return cls(
			resolved_this_week=snapshot.resolved_this_week,
			created_this_week=snapshot.created_this_week,
			avg_resolution_hours=snapshot.avg_resolution_hours,
		)
