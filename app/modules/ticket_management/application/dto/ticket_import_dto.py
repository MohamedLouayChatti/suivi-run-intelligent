from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID

from app.modules.ticket_management.application.dto.ticket_dto import TicketContentDTO
from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class TicketImportRecord:
	"""One record of an uploaded file, exactly as it was read: header -> raw cell text.

	Untyped on purpose. Whoever read the file knows how to split it into records and nothing more;
	what a column means, which are required, and how a cell becomes a `Priority` or a `datetime`
	are this module's rules, applied in one place by the import handler. A caller that coerced
	values first would be deciding half of what "valid ticket data" means.

	`line_number` is the line in the source file, header included, so a rejected record points at
	the row an operator sees in their spreadsheet rather than at an index into a list.
	"""

	line_number: int
	values: Mapping[str, str]


@dataclass(frozen=True)
class TicketImportErrorDTO:
	"""One reason one record could not become a ticket.

	`column` and `value` are absent for a failure that belongs to the record as a whole rather
	than to a single cell -- a status whose companion columns disagree, or a row duplicating
	another.
	"""

	line_number: int
	message: str
	column: str | None = None
	value: str | None = None


@dataclass(frozen=True)
class TicketImportReportDTO:
	"""What one accepted import produced.

	`contents` is the same projection a bulk pass over the whole corpus reads, in the order the
	records arrived, so the caller that has just embedded those descriptions can pair each vector
	with the ticket it now belongs to without re-reading anything.
	"""

	application: Application
	ticket_ids: tuple[UUID, ...] = field(default_factory=tuple)
	contents: tuple[TicketContentDTO, ...] = field(default_factory=tuple)
