from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class TicketCreated:
	ticket_id: UUID
	title: str
	description: str
	status: Status
	priority: Priority
	created_at: datetime
