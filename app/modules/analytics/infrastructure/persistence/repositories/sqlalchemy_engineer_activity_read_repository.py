from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.engineer_activity_dto import EngineerActivityDTO
from app.modules.analytics.application.interfaces.engineer_activity_read_repository import (
	EngineerActivityReadRepository,
)
from app.modules.analytics.application.support.time_range import DateWindow
from app.modules.analytics.infrastructure.persistence.query_helpers import (
	ACTIVE_STATUSES, DURATION_HOURS, application_filter, assignee_filter, created_in,
	ever_transferred, full_counts, not_archived, resolved_in,
)
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


class SqlAlchemyEngineerActivityReadRepository(EngineerActivityReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_engineer_activity(
		self, engineer_id: UUID, applications: frozenset[Application] | None, window: DateWindow
	) -> EngineerActivityDTO:
		scope = [assignee_filter(engineer_id)]
		app_cond = application_filter(applications)
		if app_cond is not None:
			scope.append(app_cond)

		created_cond = created_in(window)
		resolved_cond = resolved_in(window)
		active_cond = and_(TicketModel.status.in_(ACTIVE_STATUSES), not_archived())
		transferred_cond = and_(created_cond, ever_transferred())

		totals_stmt = select(
			func.count().filter(active_cond).label("active"),
			func.count().filter(created_cond).label("created"),
			func.count().filter(resolved_cond).label("resolved"),
			func.avg(DURATION_HOURS).filter(resolved_cond).label("avg_resolution_hours"),
			func.count().filter(transferred_cond).label("transferred"),
		).where(*scope)
		row = (await self.session.execute(totals_stmt)).one()

		async def grouped(column, condition):
			stmt = select(column, func.count()).where(*scope, condition).group_by(column)
			return (await self.session.execute(stmt)).all()

		return EngineerActivityDTO(
			engineer_id=engineer_id,
			active_tickets=row.active,
			created_tickets=row.created,
			resolved_tickets=row.resolved,
			avg_resolution_hours=(
				round(float(row.avg_resolution_hours), 1) if row.avg_resolution_hours is not None else 0.0
			),
			transfer_rate_pct=round(row.transferred / row.created * 100, 1) if row.created else 0.0,
			by_application=full_counts(Application, await grouped(TicketModel.application, created_cond)),
			by_category=full_counts(Category, await grouped(TicketModel.category, created_cond)),
			by_status=full_counts(Status, await grouped(TicketModel.status, created_cond)),
		)
