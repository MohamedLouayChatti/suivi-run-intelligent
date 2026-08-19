from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class TicketsImported(DomainEvent):
	"""One batch of tickets was loaded from a file, for one application, in one transaction.

	Published once for the whole batch rather than a `TicketCreated` per row, and that is a
	decision about the batch rather than an economy. `TicketCreated` announces that somebody filed
	an incident and something should react to it; a bulk historical load is one administrative act
	that happens to produce many rows. Publishing it per row would also make every consumer of that
	event do its per-ticket work a second time over data the batch pipeline has already handled in
	bulk.

	Carries the ids rather than only the count so a consumer can act on exactly what landed --
	Audit records the count, but nothing about the event assumes that is all anyone will ever want.
	"""

	application: Application
	ticket_ids: tuple[UUID, ...]
