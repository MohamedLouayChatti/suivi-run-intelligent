from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class TicketReassigned(DomainEvent):
	ticket_id: UUID
	assignee_id: UUID
	reassigned_at: datetime
	actor_id: UUID
