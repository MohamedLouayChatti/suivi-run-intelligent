from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.status import Status
from app.shared.events.event import DomainEvent

@dataclass(frozen=True)
class TicketStatusChanged(DomainEvent):
	ticket_id: UUID
	old_status: Status
	new_status: Status
	changed_at: datetime
