from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.enums.vio_app import VioApp


@dataclass(frozen=True)
class ColorisHeatmapCellDTO:
	offer: Offer
	version: Version
	count: int


@dataclass(frozen=True)
class RankedEntryDTO:
	label: Element
	count: int


@dataclass(frozen=True)
class VioAppRowDTO:
	vio_app: VioApp
	open: int
	resolved: int
	total: int


@dataclass(frozen=True)
class ApplicationInsightsDTO:
	"""Discriminated by `application`: exactly one of the three fields below is
	populated, matching which widget the frontend renders for that application
	(COLORIS -> heatmap, AERO -> top elements, VIO -> per-app rows). FCI has no
	dedicated insights and is rejected by the query."""

	application: Application
	coloris_heatmap: list[ColorisHeatmapCellDTO] | None = None
	aero_top_elements: list[RankedEntryDTO] | None = None
	vio_app_rows: list[VioAppRowDTO] | None = None
