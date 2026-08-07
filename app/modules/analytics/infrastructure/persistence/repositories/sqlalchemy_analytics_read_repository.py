from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import Date, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
from app.modules.analytics.application.dto.attention_required_dto import AgingIncidentDTO, AttentionRequiredDTO
from app.modules.analytics.application.dto.distributions_dto import DistributionsDTO
from app.modules.analytics.application.dto.jira_metrics_dto import JiraMetricsDTO
from app.modules.analytics.application.dto.kpi_snapshot_dto import KpiTotalsDTO
from app.modules.analytics.application.interfaces.analytics_read_repository import AnalyticsReadRepository
from app.modules.analytics.application.support.time_range import DateWindow, TimeRange, bucket_scheme
from app.modules.analytics.infrastructure.persistence.query_helpers import (
	ACTIVE_STATUSES, DURATION_HOURS, application_filter, created_in, full_counts, not_archived, resolved_in,
)
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


class SqlAlchemyAnalyticsReadRepository(AnalyticsReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_kpi_totals(self, applications: frozenset[Application] | None, window: DateWindow) -> KpiTotalsDTO:
		created_cond = created_in(window)
		active_created_cond = and_(created_cond, TicketModel.status.in_(ACTIVE_STATUSES))
		urgent_cond = and_(active_created_cond, TicketModel.priority == Priority.CRITICAL)
		resolved_cond = resolved_in(window)

		stmt = select(
			func.count().filter(created_cond).label("total"),
			func.count().filter(active_created_cond).label("open"),
			func.count().filter(urgent_cond).label("urgent"),
			func.count().filter(resolved_cond).label("resolved"),
			func.avg(DURATION_HOURS).filter(resolved_cond).label("avg_resolution_hours"),
		)
		app_cond = application_filter(applications)
		if app_cond is not None:
			stmt = stmt.where(app_cond)

		row = (await self.session.execute(stmt)).one()
		return KpiTotalsDTO(
			total_tickets=row.total,
			open_tickets=row.open,
			resolved_tickets=row.resolved,
			avg_resolution_hours=round(float(row.avg_resolution_hours), 1) if row.avg_resolution_hours is not None else 0.0,
			urgent_tickets=row.urgent,
		)

	async def get_activity_trend(
		self, applications: frozenset[Application] | None, time_range: TimeRange
	) -> list[ActivityPointDTO]:
		bucket_count, span_days = bucket_scheme(time_range)
		now = datetime.now(UTC)
		origin = now - timedelta(days=bucket_count * span_days)
		span_seconds = span_days * 86400
		app_cond = application_filter(applications)

		def bucket_index(column):
			return func.floor(func.extract("epoch", column - origin) / span_seconds)

		created_bucket = bucket_index(TicketModel.created_at)
		created_stmt = select(created_bucket.label("bucket"), func.count().label("count")).where(
			TicketModel.created_at >= origin, TicketModel.created_at <= now, not_archived()
		)
		resolved_bucket = bucket_index(TicketModel.resolved_at)
		resolved_stmt = select(resolved_bucket.label("bucket"), func.count().label("count")).where(
			TicketModel.resolved_at.is_not(None), TicketModel.resolved_at >= origin, TicketModel.resolved_at <= now, not_archived()
		)
		if app_cond is not None:
			created_stmt = created_stmt.where(app_cond)
			resolved_stmt = resolved_stmt.where(app_cond)
		created_stmt = created_stmt.group_by("bucket")
		resolved_stmt = resolved_stmt.group_by("bucket")

		created_by_bucket = {int(r.bucket): r.count for r in (await self.session.execute(created_stmt)).all()}
		resolved_by_bucket = {int(r.bucket): r.count for r in (await self.session.execute(resolved_stmt)).all()}

		points: list[ActivityPointDTO] = []
		for index in range(bucket_count):
			bucket_start = origin + timedelta(days=index * span_days)
			points.append(ActivityPointDTO(
				bucket_start=bucket_start,
				created=created_by_bucket.get(index, 0),
				resolved=resolved_by_bucket.get(index, 0),
			))
		return points

	async def get_distributions(self, applications: frozenset[Application] | None, window: DateWindow) -> DistributionsDTO:
		created_cond = created_in(window)
		app_cond = application_filter(applications)

		async def grouped(column):
			stmt = select(column, func.count()).where(created_cond).group_by(column)
			if app_cond is not None:
				stmt = stmt.where(app_cond)
			return (await self.session.execute(stmt)).all()

		return DistributionsDTO(
			by_status=full_counts(Status, await grouped(TicketModel.status)),
			by_category=full_counts(Category, await grouped(TicketModel.category)),
			by_priority=full_counts(Priority, await grouped(TicketModel.priority)),
		)

	async def get_jira_metrics(self, applications: frozenset[Application] | None, window: DateWindow) -> JiraMetricsDTO:
		requires_jira_cond = and_(created_in(window), TicketModel.requires_jira.is_(True))
		awaiting_cond = and_(requires_jira_cond, TicketModel.jira_delivery_date.is_(None))
		delivered_cond = and_(requires_jira_cond, TicketModel.jira_delivery_date.is_not(None))
		delivery_delay_days = TicketModel.jira_delivery_date - cast(TicketModel.created_at, Date)

		stmt = select(
			func.count().filter(requires_jira_cond).label("requires_jira"),
			func.count().filter(awaiting_cond).label("awaiting_delivery"),
			func.avg(delivery_delay_days).filter(delivered_cond).label("avg_delivery_delay_days"),
		)
		app_cond = application_filter(applications)
		if app_cond is not None:
			stmt = stmt.where(app_cond)

		row = (await self.session.execute(stmt)).one()
		return JiraMetricsDTO(
			requires_jira=row.requires_jira,
			awaiting_delivery=row.awaiting_delivery,
			avg_delivery_delay_days=round(float(row.avg_delivery_delay_days), 1) if row.avg_delivery_delay_days is not None else 0.0,
		)

	async def get_attention_required(
		self, applications: frozenset[Application] | None, threshold_days: int
	) -> AttentionRequiredDTO:
		now = datetime.now(UTC)
		cutoff = now - timedelta(days=threshold_days)
		cond = and_(TicketModel.status.in_(ACTIVE_STATUSES), TicketModel.created_at <= cutoff, not_archived())
		app_cond = application_filter(applications)
		if app_cond is not None:
			cond = and_(cond, app_cond)

		count = await self.session.scalar(select(func.count()).where(cond))

		top_stmt = (
			select(TicketModel.id, TicketModel.title, TicketModel.created_at, TicketModel.priority, TicketModel.assignee_id)
			.where(cond)
			.order_by(TicketModel.created_at.asc())
			.limit(10)
		)
		rows = (await self.session.execute(top_stmt)).all()
		incidents = [
			AgingIncidentDTO(
				ticket_id=row.id,
				title=row.title,
				age_days=(now - row.created_at).days,
				priority=row.priority,
				assignee_id=row.assignee_id,
			)
			for row in rows
		]
		return AttentionRequiredDTO(count=count or 0, threshold_days=threshold_days, incidents=incidents)
