from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class SimilarityResultsGenerated(DomainEvent):
	"""Published once the similarity pipeline persists results for a ticket. actor_id is always
	None -- produced by an async pipeline reacting to TicketCreated, not by an authenticated
	CurrentUser (same precedent as UserCreated/UserUpdated). Nothing subscribes yet..
	"""

	ticket_id: UUID
	result_count: int
