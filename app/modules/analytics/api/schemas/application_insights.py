from __future__ import annotations

from pydantic import BaseModel

from app.modules.analytics.application.dto.application_insights_dto import (
	ApplicationInsightsDTO, ColorisHeatmapCellDTO, RankedEntryDTO, VioAppRowDTO,
)
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.enums.vio_app import VioApp


class ColorisHeatmapCellResponse(BaseModel):
	offer: Offer
	version: Version
	count: int

	@classmethod
	def from_dto(cls, cell: ColorisHeatmapCellDTO) -> ColorisHeatmapCellResponse:
		return cls(offer=cell.offer, version=cell.version, count=cell.count)


class RankedEntryResponse(BaseModel):
	label: Element
	count: int

	@classmethod
	def from_dto(cls, entry: RankedEntryDTO) -> RankedEntryResponse:
		return cls(label=entry.label, count=entry.count)


class VioAppRowResponse(BaseModel):
	vio_app: VioApp
	open: int
	resolved: int
	total: int

	@classmethod
	def from_dto(cls, row: VioAppRowDTO) -> VioAppRowResponse:
		return cls(vio_app=row.vio_app, open=row.open, resolved=row.resolved, total=row.total)


class ApplicationInsightsResponse(BaseModel):
	application: Application
	coloris_heatmap: list[ColorisHeatmapCellResponse] | None
	aero_top_elements: list[RankedEntryResponse] | None
	vio_app_rows: list[VioAppRowResponse] | None

	@classmethod
	def from_dto(cls, insights: ApplicationInsightsDTO) -> ApplicationInsightsResponse:
		return cls(
			application=insights.application,
			coloris_heatmap=(
				[ColorisHeatmapCellResponse.from_dto(cell) for cell in insights.coloris_heatmap]
				if insights.coloris_heatmap is not None else None
			),
			aero_top_elements=(
				[RankedEntryResponse.from_dto(entry) for entry in insights.aero_top_elements]
				if insights.aero_top_elements is not None else None
			),
			vio_app_rows=(
				[VioAppRowResponse.from_dto(row) for row in insights.vio_app_rows]
				if insights.vio_app_rows is not None else None
			),
		)
