from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.application.dto.ticket_import_dto import TicketImportRecord
from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class ImportTicketsCommand:
	"""Create every ticket a file describes, or none of them.

	`application` comes from the request rather than from the records, because one file belongs to
	one application: it is the fact the uploader asserts about the whole batch, and a column
	answering the same question a second time could only ever disagree with it.

	`columns` is carried separately from the records rather than inferred from them, so a file with
	a valid header and no rows is rejected for being empty instead of for having no columns -- and
	so the header is checked once, ahead of everything, rather than being re-derived per row.

	The records are raw text. Coercing them is this command's handler's work: what a column means
	and what values it accepts are ticket rules, and a caller that resolved them first would be
	deciding half of what valid ticket data is.
	"""

	application: Application
	columns: tuple[str, ...]
	records: tuple[TicketImportRecord, ...]
	imported_at: datetime
	actor_id: UUID
