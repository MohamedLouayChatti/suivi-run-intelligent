from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum
from typing import TypeVar

from app.modules.ticket_management.application.commands.import_tickets import columns
from app.modules.ticket_management.application.commands.import_tickets.columns import normalize_header
from app.modules.ticket_management.application.dto.ticket_import_dto import (
	TicketImportErrorDTO,
	TicketImportRecord,
)
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.enums.vio_app import VioApp

EnumT = TypeVar("EnumT", bound=Enum)

# Beyond this many members, an error message that lists every accepted value stops being help and
# becomes a wall -- Offer alone has close to two hundred codes. Smaller enums are worth spelling
# out, because "P5 is not a priority" is far less useful than being told the four that are.
_MAX_LISTED_ENUM_VALUES = 16

# French spellings accepted alongside each member's own value, for the two enums whose values are
# the only English left in an otherwise French file. Everything else already reads in French or in
# codes the team uses directly: Category, Element and TransferDestination are stored in French,
# Priority is P1..P4, and Offer and Version are supplier codes.
#
# Compared after `normalize_header`, so accents, case and punctuation are already forgiven -- these
# are alternative *words*, not alternative spellings of the same word. `Paramétrage` is here because
# it is what the team's own exports write for the configuration team.
_ENUM_ALIASES: dict[type[Enum], dict[Enum, tuple[str, ...]]] = {
	Status: {
		Status.OPEN: ("Ouvert",),
		Status.IN_PROGRESS: ("En cours",),
		Status.TRANSFERRED: ("Transféré",),
		Status.RESOLVED: ("Résolu",),
		Status.CLOSED: ("Clôturé", "Fermé"),
	},
	FunctionalTeam: {
		FunctionalTeam.SUPPORT: ("Support",),
		FunctionalTeam.CONFIGURATION: ("Configuration", "Paramétrage"),
	},
}

_TRUE_SPELLINGS = frozenset({normalize_header(word) for word in ("oui", "vrai", "true")})
_FALSE_SPELLINGS = frozenset({normalize_header(word) for word in ("non", "faux", "false")})

_ALIAS_LOOKUP: dict[type[Enum], dict[str, Enum]] = {
	enum_type: {
		normalize_header(spelling): member
		for member, spellings in aliases.items()
		for spelling in spellings
	}
	for enum_type, aliases in _ENUM_ALIASES.items()
}


def _accepted_values(enum_type: type[Enum]) -> list[str]:
	"""How an enum's accepted values are spelled out in an error message.

	A member with French spellings shows them next to its stored value, because an operator looking
	at a rejected `statut` needs to see that both `RESOLVED` and `Résolu` would have worked -- being
	told only the stored value would read as though their French file was the wrong shape entirely.
	"""
	aliases = _ENUM_ALIASES.get(enum_type, {})
	values = []
	for member in enum_type:
		spellings = aliases.get(member, ())
		values.append(
			f"{member.value} ({', '.join(spellings)})" if spellings else str(member.value)
		)
	return values


@dataclass(frozen=True)
class ParsedTicketRecord:
	"""One record whose cells have been read as the types the aggregate takes.

	Not a ticket yet, and deliberately stops short of being one: the assignee is still a display
	name, because resolving names to users is a database question answered once for the whole file
	rather than once per row, and the conditional-field rules are still unchecked, because the
	aggregate owns those and re-stating them here would be a second copy free to drift.
	"""

	line_number: int
	title: str
	description: str
	priority: Priority
	category: Category
	functional_team: FunctionalTeam
	assignee_name: str
	created_at: datetime
	status: Status
	genergy_id: str | None
	oceane_id: str | None
	requires_jira: bool
	jira_id: str | None
	jira_delivery_date: date | None
	operational_highlight: bool
	offer: Offer | None
	version: Version | None
	element: Element | None
	vio_app: VioApp | None
	resolved_at: datetime | None
	closed_at: datetime | None
	resolution_notes: str | None
	transferred_to: TransferDestination | None


class _RecordReader:
	"""Reads one record's cells, collecting every failure instead of stopping at the first.

	An operator fixing an export wants the whole list of what is wrong with a row, not to discover
	its four problems over four uploads -- so each accessor returns a usable placeholder on failure
	and records why, and the caller checks `errors` once at the end.
	"""

	def __init__(self, record: TicketImportRecord) -> None:
		self.record = record
		self.errors: list[TicketImportErrorDTO] = []

	def _cell(self, column: str) -> str:
		return (self.record.values.get(column) or "").strip()

	def _fail(self, column: str, value: str, message: str) -> None:
		self.errors.append(
			TicketImportErrorDTO(
				line_number=self.record.line_number, message=message, column=column, value=value or None
			)
		)

	def required_text(self, column: str) -> str:
		value = self._cell(column)
		if not value:
			self._fail(column, value, f"{column} is required and must not be empty.")
		return value

	def optional_text(self, column: str) -> str | None:
		return self._cell(column) or None

	def required_enum(self, column: str, enum_type: type[EnumT]) -> EnumT | None:
		if not self._cell(column):
			self._fail(column, "", f"{column} is required and must not be empty.")
			return None
		return self.optional_enum(column, enum_type)

	def optional_enum(self, column: str, enum_type: type[EnumT]) -> EnumT | None:
		value = self._cell(column)
		if not value:
			return None
		try:
			return enum_type(value)
		except ValueError:
			pass

		alias = _ALIAS_LOOKUP.get(enum_type, {}).get(normalize_header(value))
		if alias is not None:
			return alias  # type: ignore[return-value]

		members = _accepted_values(enum_type)
		listed = ", ".join(members) if len(members) <= _MAX_LISTED_ENUM_VALUES else ""
		detail = f" Accepted values: {listed}." if listed else ""
		self._fail(column, value, f"{value} is not a valid {column}.{detail}")
		return None

	def optional_flag(self, column: str) -> bool:
		"""Absent means false; otherwise the spellings a French sheet actually contains.

		`oui`/`non` because that is what someone types, `vrai`/`faux` because that is what a French
		Excel writes for a real boolean cell, and `true`/`false` because that is what the workbook
		reader produces from one. Numeric 1 and 0 are deliberately *not* accepted: a column of
		digits is as likely to be a count or a flag inverted by whoever built the sheet, and
		guessing is how a column silently comes to mean the opposite of what it says.
		"""
		value = self._cell(column)
		if not value:
			return False
		normalized = normalize_header(value)
		if normalized in _TRUE_SPELLINGS:
			return True
		if normalized in _FALSE_SPELLINGS:
			return False
		self._fail(
			column, value,
			f"{column} must be one of oui, non, vrai, faux, true, false -- or empty, which means non.",
		)
		return False

	def required_datetime(self, column: str) -> datetime | None:
		if not self._cell(column):
			self._fail(column, "", f"{column} is required and must not be empty.")
			return None
		return self.optional_datetime(column)

	def optional_datetime(self, column: str) -> datetime | None:
		"""ISO-8601 only, and a value carrying no timezone is read as UTC.

		One format rather than a list of tolerated ones, because a date is the field where a
		lenient parser does the most damage: 03/04/2025 is two different days depending on who
		exported it, and neither reading is detectable afterwards. A bare date is accepted and
		means midnight, which is the one shortening that cannot be ambiguous.
		"""
		value = self._cell(column)
		if not value:
			return None
		try:
			parsed = datetime.fromisoformat(value)
		except ValueError:
			self._fail(
				column, value,
				f"{value} is not a valid ISO-8601 date or timestamp "
				f"(for example 2025-10-01 or 2025-10-01T14:30:00Z).",
			)
			return None
		return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

	def optional_date(self, column: str) -> date | None:
		value = self._cell(column)
		if not value:
			return None
		try:
			return date.fromisoformat(value)
		except ValueError:
			self._fail(column, value, f"{value} is not a valid ISO-8601 date (for example 2025-10-01).")
			return None

	def record_error(self, message: str) -> None:
		"""A failure belonging to the record as a whole rather than to any one cell."""
		self.errors.append(TicketImportErrorDTO(line_number=self.record.line_number, message=message))


def parse_record(record: TicketImportRecord) -> tuple[ParsedTicketRecord | None, list[TicketImportErrorDTO]]:
	"""Read one record into the types the aggregate takes, or report everything wrong with it.

	Returns a record and no errors, or no record and at least one error -- never a half-usable one,
	since a batch that is rejected as a whole has no use for a partially readable row.
	"""
	reader = _RecordReader(record)

	title = reader.required_text(columns.TITLE)
	description = reader.required_text(columns.DESCRIPTION)
	priority = reader.required_enum(columns.PRIORITY, Priority)
	category = reader.required_enum(columns.CATEGORY, Category)
	functional_team = reader.required_enum(columns.FUNCTIONAL_TEAM, FunctionalTeam)
	assignee_name = reader.required_text(columns.ASSIGNEE)
	created_at = reader.required_datetime(columns.CREATED_AT)

	status = reader.optional_enum(columns.STATUS, Status) or Status.OPEN
	resolved_at = reader.optional_datetime(columns.RESOLVED_AT)
	closed_at = reader.optional_datetime(columns.CLOSED_AT)
	resolution_notes = reader.optional_text(columns.RESOLUTION_NOTES)
	transferred_to = reader.optional_enum(columns.TRANSFERRED_TO, TransferDestination)

	genergy_id = reader.optional_text(columns.GENERGY_ID)
	oceane_id = reader.optional_text(columns.OCEANE_ID)
	requires_jira = reader.optional_flag(columns.REQUIRES_JIRA)
	jira_id = reader.optional_text(columns.JIRA_ID)
	jira_delivery_date = reader.optional_date(columns.JIRA_DELIVERY_DATE)
	operational_highlight = reader.optional_flag(columns.OPERATIONAL_HIGHLIGHT)
	offer = reader.optional_enum(columns.OFFER, Offer)
	version = reader.optional_enum(columns.VERSION, Version)
	element = reader.optional_enum(columns.ELEMENT, Element)
	vio_app = reader.optional_enum(columns.VIO_APP, VioApp)

	_validate_lifecycle(reader, status, resolved_at, closed_at, resolution_notes, transferred_to)
	_validate_chronology(reader, created_at, resolved_at, closed_at)

	if reader.errors:
		return None, reader.errors

	# Everything below is known to have parsed; the guard only states for the type checker what the
	# empty error list already guarantees.
	if priority is None or category is None or functional_team is None or created_at is None:
		return None, reader.errors

	return (
		ParsedTicketRecord(
			line_number=record.line_number,
			title=title,
			description=description,
			priority=priority,
			category=category,
			functional_team=functional_team,
			assignee_name=assignee_name,
			created_at=created_at,
			status=status,
			genergy_id=genergy_id,
			oceane_id=oceane_id,
			requires_jira=requires_jira,
			jira_id=jira_id,
			jira_delivery_date=jira_delivery_date,
			operational_highlight=operational_highlight,
			offer=offer,
			version=version,
			element=element,
			vio_app=vio_app,
			resolved_at=resolved_at,
			closed_at=closed_at,
			resolution_notes=resolution_notes,
			transferred_to=transferred_to,
		),
		[],
	)


def _validate_lifecycle(
	reader: _RecordReader,
	status: Status,
	resolved_at: datetime | None,
	closed_at: datetime | None,
	resolution_notes: str | None,
	transferred_to: TransferDestination | None,
) -> None:
	"""Whether the lifecycle columns describe the status the row claims.

	Checked here rather than left to the aggregate because the aggregate is reached by *replaying*
	the transitions, and a row claiming RESOLVED with no resolution date has no replay to attempt
	-- there is nothing to hand to resolve(). What the aggregate does own, and what is therefore
	not restated here, is whether each transition is legal and whether the conditional application
	fields agree with each other.
	"""
	resolution_columns: dict[str, object | None] = {
		columns.RESOLVED_AT: resolved_at,
		columns.RESOLUTION_NOTES: resolution_notes,
	}
	forbidden_by_status: dict[Status, dict[str, object | None]] = {
		Status.OPEN: {
			**resolution_columns,
			columns.CLOSED_AT: closed_at,
			columns.TRANSFERRED_TO: transferred_to,
		},
		Status.IN_PROGRESS: {
			**resolution_columns,
			columns.CLOSED_AT: closed_at,
			columns.TRANSFERRED_TO: transferred_to,
		},
		Status.TRANSFERRED: {**resolution_columns, columns.CLOSED_AT: closed_at},
		Status.RESOLVED: {columns.CLOSED_AT: closed_at, columns.TRANSFERRED_TO: transferred_to},
		Status.CLOSED: {},
	}

	for column, value in forbidden_by_status[status].items():
		if value is not None:
			reader.record_error(f"{column} must be empty for a ticket with status {status.value}.")

	if status == Status.TRANSFERRED and transferred_to is None:
		reader.record_error(
			f"{columns.TRANSFERRED_TO} is required for a ticket with status {Status.TRANSFERRED.value}."
		)

	if status == Status.RESOLVED:
		_require_resolution(reader, status, resolved_at, resolution_notes)

	if status == Status.CLOSED:
		if closed_at is None:
			reader.record_error(
				f"{columns.CLOSED_AT} is required for a ticket with status {Status.CLOSED.value}."
			)
		# A closed ticket reached that state from exactly one of two places, and the file has to
		# say which: it was resolved, or it was transferred away. Both at once describes no history
		# the aggregate can replay, and neither leaves the close with nothing to follow.
		if transferred_to is not None:
			for column, value in resolution_columns.items():
				if value is not None:
					reader.record_error(
						f"{column} must be empty for a ticket closed after being transferred: a "
						f"closed ticket was either resolved or transferred, not both."
					)
		else:
			_require_resolution(reader, status, resolved_at, resolution_notes)


def _require_resolution(
	reader: _RecordReader, status: Status, resolved_at: datetime | None, resolution_notes: str | None
) -> None:
	if resolved_at is None:
		reader.record_error(
			f"{columns.RESOLVED_AT} is required for a ticket with status {status.value} that was "
			f"not transferred."
		)
	if not resolution_notes:
		reader.record_error(
			f"{columns.RESOLUTION_NOTES} is required for a ticket with status {status.value} that "
			f"was not transferred."
		)


def _validate_chronology(
	reader: _RecordReader,
	created_at: datetime | None,
	resolved_at: datetime | None,
	closed_at: datetime | None,
) -> None:
	"""The aggregate refuses a transition dated before the one preceding it, and would do so here
	as an opaque ChronologicalOrderViolation raised from some replayed step. Naming the two columns
	that disagree is the difference between a fixable message and a puzzle.
	"""
	if created_at is None:
		return
	if resolved_at is not None and resolved_at < created_at:
		reader.record_error(f"{columns.RESOLVED_AT} is earlier than {columns.CREATED_AT}.")
	if closed_at is not None and closed_at < created_at:
		reader.record_error(f"{columns.CLOSED_AT} is earlier than {columns.CREATED_AT}.")
	if resolved_at is not None and closed_at is not None and closed_at < resolved_at:
		reader.record_error(f"{columns.CLOSED_AT} is earlier than {columns.RESOLVED_AT}.")
