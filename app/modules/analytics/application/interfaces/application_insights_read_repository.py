from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.analytics.application.dto.application_insights_dto import (
	ColorisHeatmapCellDTO, RankedEntryDTO, VioAppRowDTO,
)
from app.modules.analytics.application.support.time_range import DateWindow
from app.modules.ticket_management.domain.enums.application import Application


class ApplicationInsightsReadRepository(ABC):
	"""Backs the per-application insight widgets (COLORIS heatmap, AERO top elements,
	VIO app rows) -- each scoped to a single application's created-in-period cohort."""

	@abstractmethod
	async def get_coloris_heatmap(self, application: Application, window: DateWindow) -> list[ColorisHeatmapCellDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_aero_top_elements(self, application: Application, window: DateWindow) -> list[RankedEntryDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_vio_app_rows(self, application: Application, window: DateWindow) -> list[VioAppRowDTO]:
		raise NotImplementedError
