from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.admin_overview_dto import (
	AppJiraDependencyDTO, AppMonthlyTrendPointDTO, AppResolutionTimeDTO, AppTransferRateDTO,
	AppWorkloadRowDTO, EngineerDatumDTO, TeamOverviewDTO,
)
from app.modules.analytics.application.dto.health_signal_dto import ApplicationHealthSignalDTO
from app.modules.analytics.application.interfaces.admin_analytics_read_repository import AdminAnalyticsReadRepository
from app.modules.analytics.application.support.time_range import DateWindow
from app.modules.analytics.infrastructure.persistence.query_helpers import (
	ACTIVE_STATUSES, DURATION_HOURS, created_in, ever_transferred, not_archived, resolved_in,
)
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


class SqlAlchemyAdminAnalyticsReadRepository(AdminAnalyticsReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_workload(self, window: DateWindow) -> list[AppWorkloadRowDTO]:
		created_cond = created_in(window)
		stmt = select(
			TicketModel.application,
			func.count().filter(and_(created_cond, TicketModel.status == Status.OPEN)).label("open"),
			func.count().filter(and_(created_cond, TicketModel.status == Status.IN_PROGRESS)).label("in_progress"),
			func.count().filter(resolved_in(window)).label("resolved"),
		).where(created_cond).group_by(TicketModel.application)
		rows = {row.application: row for row in (await self.session.execute(stmt)).all()}
		return [
			AppWorkloadRowDTO(
				application=app,
				open=rows[app].open if app in rows else 0,
				in_progress=rows[app].in_progress if app in rows else 0,
				resolved=rows[app].resolved if app in rows else 0,
			)
			for app in Application
		]

	async def get_health(self, window: DateWindow) -> list[ApplicationHealthSignalDTO]:
		active_cond = and_(TicketModel.status.in_(ACTIVE_STATUSES), not_archived())

		live_stmt = select(
			TicketModel.application,
			func.count().filter(active_cond).label("active"),
			func.count().filter(and_(active_cond, TicketModel.priority == Priority.CRITICAL)).label("urgent"),
		).group_by(TicketModel.application)
		live_rows = {row.application: row for row in (await self.session.execute(live_stmt)).all()}

		resolution_stmt = select(
			TicketModel.application, func.avg(DURATION_HOURS).filter(resolved_in(window)).label("avg_resolution_hours")
		).where(resolved_in(window)).group_by(TicketModel.application)
		resolution_rows = {row.application: row.avg_resolution_hours for row in (await self.session.execute(resolution_stmt)).all()}

		results: list[ApplicationHealthSignalDTO] = []
		for app in Application:
			live = live_rows.get(app)
			active = live.active if live else 0
			urgent = live.urgent if live else 0
			avg_resolution_hours = round(float(resolution_rows.get(app) or 0.0), 1)
			results.append(ApplicationHealthSignalDTO(
				application=app, active_tickets=active,
				avg_resolution_hours=avg_resolution_hours, urgent_tickets=urgent,
			))
		return results

	async def get_health_signal(self, application: Application, window: DateWindow) -> ApplicationHealthSignalDTO:
		active_cond = and_(TicketModel.status.in_(ACTIVE_STATUSES), not_archived(), TicketModel.application == application)

		live_stmt = select(
			func.count().filter(active_cond).label("active"),
			func.count().filter(and_(active_cond, TicketModel.priority == Priority.CRITICAL)).label("urgent"),
		)
		live_row = (await self.session.execute(live_stmt)).one()

		resolution_stmt = select(func.avg(DURATION_HOURS)).where(resolved_in(window), TicketModel.application == application)
		avg_resolution_hours = round(float((await self.session.execute(resolution_stmt)).scalar() or 0.0), 1)

		return ApplicationHealthSignalDTO(
			application=application, active_tickets=live_row.active,
			avg_resolution_hours=avg_resolution_hours, urgent_tickets=live_row.urgent,
		)

	async def get_resolution_time_comparison(self, window: DateWindow) -> list[AppResolutionTimeDTO]:
		stmt = select(
			TicketModel.application, func.avg(DURATION_HOURS).filter(resolved_in(window)).label("avg_resolution_hours")
		).where(resolved_in(window)).group_by(TicketModel.application)
		rows = {row.application: row.avg_resolution_hours for row in (await self.session.execute(stmt)).all()}
		return [
			AppResolutionTimeDTO(application=app, avg_resolution_hours=round(float(rows.get(app) or 0.0), 1))
			for app in Application
		]

	async def get_jira_dependency(self, window: DateWindow) -> list[AppJiraDependencyDTO]:
		cond = and_(created_in(window), TicketModel.requires_jira.is_(True))
		stmt = select(TicketModel.application, func.count().label("count")).where(cond).group_by(TicketModel.application)
		rows = {row.application: row.count for row in (await self.session.execute(stmt)).all()}
		return [AppJiraDependencyDTO(application=app, jira_incidents=rows.get(app, 0)) for app in Application]

	async def get_transfer_rate(self, window: DateWindow) -> list[AppTransferRateDTO]:
		created_cond = created_in(window)
		stmt = select(
			TicketModel.application,
			func.count().label("total"),
			func.count().filter(ever_transferred()).label("transferred"),
		).where(created_cond).group_by(TicketModel.application)
		rows = {row.application: row for row in (await self.session.execute(stmt)).all()}
		results = []
		for app in Application:
			row = rows.get(app)
			total = row.total if row else 0
			transferred = row.transferred if row else 0
			pct = round(transferred / total * 100, 1) if total > 0 else 0.0
			results.append(AppTransferRateDTO(application=app, transfer_rate_pct=pct))
		return results

	async def get_monthly_trends(self) -> list[AppMonthlyTrendPointDTO]:
		now = datetime.now(UTC)
		current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		# 11 full months back + the current one = 12 trailing calendar months.
		months = [_shift_month(current_month_start, -offset) for offset in range(11, -1, -1)]
		origin = months[0]

		month_col = func.date_trunc("month", TicketModel.created_at)
		stmt = (
			select(month_col.label("month"), TicketModel.application, func.count().label("count"))
			.where(TicketModel.created_at >= origin, not_archived())
			.group_by("month", TicketModel.application)
		)
		rows = (await self.session.execute(stmt)).all()
		# Keyed by (year, month) rather than the raw timestamp -- avoids relying on the
		# DB driver returning date_trunc's result in a specific tzinfo representation.
		counts_by_month: dict[tuple[int, int], dict[Application, int]] = {}
		for row in rows:
			counts_by_month.setdefault((row.month.year, row.month.month), {})[row.application] = row.count

		return [
			AppMonthlyTrendPointDTO(
				month=month.date(), counts=dict.fromkeys(Application, 0) | counts_by_month.get((month.year, month.month), {})
			)
			for month in months
		]

	async def get_team_overview(self, window: DateWindow) -> TeamOverviewDTO:
		active_cond = and_(TicketModel.status.in_(ACTIVE_STATUSES), not_archived())
		active_stmt = select(TicketModel.assignee_id, func.count().label("value")).where(active_cond).group_by(TicketModel.assignee_id)

		resolved_cond = resolved_in(window)
		resolved_stmt = select(
			TicketModel.assignee_id,
			func.count().label("resolved"),
			func.avg(DURATION_HOURS).label("avg_resolution_hours"),
		).where(resolved_cond).group_by(TicketModel.assignee_id)

		created_cond = created_in(window)
		assignment_stmt = select(TicketModel.assignee_id, func.count().label("value")).where(created_cond).group_by(TicketModel.assignee_id)

		transfer_stmt = select(
			TicketModel.assignee_id,
			func.count().label("total"),
			func.count().filter(ever_transferred()).label("transferred"),
		).where(created_cond).group_by(TicketModel.assignee_id)

		active_rows = (await self.session.execute(active_stmt)).all()
		resolved_rows = (await self.session.execute(resolved_stmt)).all()
		assignment_rows = (await self.session.execute(assignment_stmt)).all()
		transfer_rows = (await self.session.execute(transfer_stmt)).all()

		return TeamOverviewDTO(
			active_tickets=[EngineerDatumDTO(engineer_id=row.assignee_id, value=row.value) for row in active_rows],
			resolved_tickets=[EngineerDatumDTO(engineer_id=row.assignee_id, value=row.resolved) for row in resolved_rows],
			avg_resolution_hours=[
				EngineerDatumDTO(engineer_id=row.assignee_id, value=round(float(row.avg_resolution_hours or 0.0), 1))
				for row in resolved_rows
			],
			assignment_distribution=[EngineerDatumDTO(engineer_id=row.assignee_id, value=row.value) for row in assignment_rows],
			transfer_rate_pct=[
				EngineerDatumDTO(engineer_id=row.assignee_id, value=round(row.transferred / row.total * 100, 1) if row.total else 0.0)
				for row in transfer_rows
			],
		)


def _shift_month(value: datetime, offset: int) -> datetime:
	month_index = value.month - 1 + offset
	year = value.year + month_index // 12
	month = month_index % 12 + 1
	return value.replace(year=year, month=month)
