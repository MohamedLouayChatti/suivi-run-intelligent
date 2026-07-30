from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.enums.vio_app import VioApp

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "processed"
PROCESSED_FILES = ("FCI.json", "COLORIS.json", "AERO.json", "VIO.json")

# A handful of historical tickets have no recorded acteur; assigned to this
# fallback user since Ticket.assignee_id is mandatory.
FALLBACK_ACTEUR = "TERCHELLAH Rim"


@dataclass(frozen=True, slots=True)
class ProcessedTicket:
	"""A historical ticket exactly as normalized in data/processed/*.json."""

	genergy_id: str | None
	oceane_id: str | None
	title: str
	description: str
	application: Application
	priority: Priority
	category: Category
	functional_team: FunctionalTeam
	acteur: str
	created_at: datetime
	resolved_at: datetime | None
	closed_at: datetime
	resolution_notes: str | None
	transferred_to: TransferDestination | None
	original_status: str
	jira_id: str | None
	requires_jira: bool
	jira_delivery_date: date | None
	operational_highlight: bool
	offer: Offer | None
	version: Version | None
	element: Element | None
	vio_app: VioApp | None


def load_processed_tickets() -> list[ProcessedTicket]:
	tickets: list[ProcessedTicket] = []
	for filename in PROCESSED_FILES:
		with (DATA_DIR / filename).open(encoding="utf-8") as fh:
			rows = json.load(fh)
		tickets.extend(_parse_row(row) for row in rows)
	return tickets


def _parse_row(row: dict) -> ProcessedTicket:
	application = Application(row["application"])
	is_coloris = application == Application.COLORIS
	return ProcessedTicket(
		genergy_id=row["genergy_id"],
		oceane_id=row["oceane_id"],
		title=row["title"],
		description=row["description"],
		application=application,
		priority=Priority(row["priority"]),
		category=Category(row["category"]),
		functional_team=FunctionalTeam(row["functional_team"]),
		acteur=row["acteur"].strip() if row["acteur"] is not None else FALLBACK_ACTEUR,
		created_at=_parse_datetime(row["created_at"]),
		resolved_at=_parse_optional_datetime(row["resolved_at"]),
		closed_at=_parse_datetime(row["closed_at"]),
		resolution_notes=row["resolution_notes"],
		transferred_to=_parse_optional_enum(TransferDestination, row["transferred_to"]),
		original_status=row["original_status"],
		jira_id=row["jira_id"],
		requires_jira=row["requires_jira"],
		jira_delivery_date=_parse_optional_date(row["jira_delivery_date"]),
		operational_highlight=row["operational_highlight"],
		offer=_parse_offer(row["offer"], required=is_coloris),
		version=_parse_version(row["version"], required=is_coloris),
		element=_parse_optional_enum(Element, row["element"]),
		vio_app=_parse_optional_enum(VioApp, row["vio_app"]),
	)


def _parse_datetime(value: str) -> datetime:
	return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
	return _parse_datetime(value) if value is not None else None


def _parse_optional_date(value: str | None) -> date | None:
	return date.fromisoformat(value) if value is not None else None


def _parse_optional_enum(enum_cls: type, value: str | None) -> object | None:
	return enum_cls(value) if value is not None else None


def _parse_offer(value: str | None, *, required: bool) -> Offer | None:
	if value is None:
		return Offer.NOT_SPECIFIED if required else None
	try:
		return Offer(value)
	except ValueError:
		# A handful of historical offer codes have no matching enum member.
		return Offer.NOT_SPECIFIED


def _parse_version(value: str | None, *, required: bool) -> Version | None:
	if value is None:
		return Version.NOT_SPECIFIED if required else None
	return Version(value)
