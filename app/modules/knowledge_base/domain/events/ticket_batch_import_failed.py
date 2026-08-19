from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class TicketBatchImportFailed(DomainEvent):
	"""A batch of tickets was created and then could not be brought into the knowledge base.

	Published only on the failure path, deliberately. A successful import is already recorded by
	Ticket Management's own TicketsImported, and a second event for the same act would put two rows
	in the audit log where one thing happened.

	tickets_discarded is why this event exists at all. When the compensation succeeds, the
	preceding TicketsImported is followed by TicketsImportDiscarded and the log reads correctly on
	its own. When the compensation *itself* fails, that second event is never published -- the
	handler that would have published it is the one that raised -- and the audit log is left
	showing an import and nothing else, which is indistinguishable from an import that worked. In
	fact the tickets are sitting in the database with no corpus entry behind them, invisible to
	every similarity search, and the repair is a backfill rather than another upload. That
	distinction reaches the operator in one HTTP response today and nowhere else; if they close the
	tab, it is gone.

	Ticket ids are counted rather than listed, matching TicketsImported's reasoning: a payload
	holding a thousand UUIDs would dwarf every other row in the table, and what a reader needs here
	is how much was left behind and where to look for it.
	"""

	application: Application
	ticket_count: int
	reason: str
	tickets_discarded: bool
