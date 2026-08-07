from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
from app.modules.analytics.application.dto.my_kpi_snapshot_dto import MyKpiSnapshotDTO
from app.modules.analytics.application.interfaces.personal_analytics_read_repository import (
	PersonalAnalyticsReadRepository,
)
from app.modules.analytics.application.support.time_range import DateWindow, TimeRange, bucket_scheme
from app.modules.analytics.infrastructure.persistence.query_helpers import (
	DURATION_HOURS, assignee_filter, bucketed_activity_trend, created_in, resolved_in,
)


class SqlAlchemyPersonalAnalyticsReadRepository(PersonalAnalyticsReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_my_kpi_totals(self, assignee_id: UUID, window: DateWindow) -> MyKpiSnapshotDTO:
		created_cond = created_in(window)
		resolved_cond = resolved_in(window)

		stmt = select(
			func.count().filter(created_cond).label("created"),
			func.count().filter(resolved_cond).label("resolved"),
			func.avg(DURATION_HOURS).filter(resolved_cond).label("avg_resolution_hours"),
		).where(assignee_filter(assignee_id))

		row = (await self.session.execute(stmt)).one()
		return MyKpiSnapshotDTO(
			resolved_this_week=row.resolved,
			created_this_week=row.created,
			avg_resolution_hours=round(float(row.avg_resolution_hours), 1) if row.avg_resolution_hours is not None else 0.0,
		)

	async def get_my_activity_trend(self, assignee_id: UUID) -> list[ActivityPointDTO]:
		bucket_count, span_days = bucket_scheme(TimeRange.LAST_30_DAYS)
		return await bucketed_activity_trend(
			self.session, extra_condition=assignee_filter(assignee_id), bucket_count=bucket_count, span_days=span_days
		)
