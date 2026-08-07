from __future__ import annotations

from app.modules.analytics.application.dto.application_insights_dto import ApplicationInsightsDTO
from app.modules.analytics.application.exceptions import UnsupportedInsightsApplication
from app.modules.analytics.application.interfaces.application_insights_read_repository import (
	ApplicationInsightsReadRepository,
)
from app.modules.analytics.application.queries.get_application_insights.query import GetApplicationInsightsQuery
from app.modules.analytics.application.support.time_range import resolve_window
from app.modules.ticket_management.domain.enums.application import Application


class GetApplicationInsightsHandler:
	def __init__(self, repository: ApplicationInsightsReadRepository) -> None:
		self.repository = repository

	async def handle(self, query: GetApplicationInsightsQuery) -> ApplicationInsightsDTO:
		window = resolve_window(query.time_range).current
		application = query.application

		if application == Application.COLORIS:
			cells = await self.repository.get_coloris_heatmap(application, window)
			return ApplicationInsightsDTO(application=application, coloris_heatmap=cells)
		if application == Application.AERO:
			elements = await self.repository.get_aero_top_elements(application, window)
			return ApplicationInsightsDTO(application=application, aero_top_elements=elements)
		if application == Application.VIO:
			rows = await self.repository.get_vio_app_rows(application, window)
			return ApplicationInsightsDTO(application=application, vio_app_rows=rows)

		raise UnsupportedInsightsApplication(application)
