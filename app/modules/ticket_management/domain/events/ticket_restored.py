from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.events.event import DomainEvent

@dataclass(frozen=True)
class TicketRestored(DomainEvent):
	ticket_id: UUID
	restored_at: datetime
	actor_id: UUID
