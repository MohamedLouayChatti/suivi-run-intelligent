from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class DiscardImportedTicketsCommand:
	"""Undo a batch import whose caller could not complete what it had started.

	The compensating half of ImportTicketsCommand, and the only place in this module where tickets
	are genuinely deleted rather than archived. That is deliberate and narrow: archival is what
	happens to a ticket that existed and stopped being relevant, whereas these tickets were part of
	an operation that failed, were never seen by anyone, and were promised to be all-or-nothing.
	Leaving them archived would leave the file half-applied under a different name.

	Takes the ids the import returned rather than a batch identifier: the caller holds exactly what
	it created, and nothing here needs a record of imports to look one up in.
	"""

	ticket_ids: tuple[UUID, ...]
	application: Application
	reason: str
	discarded_at: datetime
	actor_id: UUID
