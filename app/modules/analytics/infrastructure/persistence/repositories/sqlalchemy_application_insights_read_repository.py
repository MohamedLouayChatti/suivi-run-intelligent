from __future__ import annotations

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.application_insights_dto import (
	ColorisHeatmapCellDTO, RankedEntryDTO, VioAppRowDTO,
)
from app.modules.analytics.application.interfaces.application_insights_read_repository import (
	ApplicationInsightsReadRepository,
)
from app.modules.analytics.application.support.time_range import DateWindow
from app.modules.analytics.infrastructure.persistence.query_helpers import created_in
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel

_AERO_TOP_ELEMENTS_LIMIT = 7


class SqlAlchemyApplicationInsightsReadRepository(ApplicationInsightsReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_coloris_heatmap(self, application: Application, window: DateWindow) -> list[ColorisHeatmapCellDTO]:
		stmt = (
			select(TicketModel.offer, TicketModel.version, func.count().label("count"))
			.where(created_in(window), TicketModel.application == application)
			.group_by(TicketModel.offer, TicketModel.version)
		)
		rows = (await self.session.execute(stmt)).all()
		return [ColorisHeatmapCellDTO(offer=row.offer, version=row.version, count=row.count) for row in rows]

	async def get_aero_top_elements(self, application: Application, window: DateWindow) -> list[RankedEntryDTO]:
		stmt = (
			select(TicketModel.element, func.count().label("count"))
			.where(created_in(window), TicketModel.application == application)
			.group_by(TicketModel.element)
			.order_by(func.count().desc())
			.limit(_AERO_TOP_ELEMENTS_LIMIT)
		)
		rows = (await self.session.execute(stmt)).all()
		return [RankedEntryDTO(label=row.element, count=row.count) for row in rows]

	async def get_vio_app_rows(self, application: Application, window: DateWindow) -> list[VioAppRowDTO]:
		cohort = and_(created_in(window), TicketModel.application == application)
		open_statuses = (Status.OPEN, Status.IN_PROGRESS)
		resolved_statuses = (Status.RESOLVED, Status.CLOSED)
		stmt = (
			select(
				TicketModel.vio_app,
				func.count().filter(TicketModel.status.in_(open_statuses)).label("open"),
				func.count().filter(TicketModel.status.in_(resolved_statuses)).label("resolved"),
			)
			.where(cohort)
			.group_by(TicketModel.vio_app)
		)
		rows = (await self.session.execute(stmt)).all()
		return [
			VioAppRowDTO(vio_app=row.vio_app, open=row.open, resolved=row.resolved, total=row.open + row.resolved)
			for row in rows
		]
