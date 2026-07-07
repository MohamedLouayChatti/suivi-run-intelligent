from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority


@dataclass(frozen=True)
class CreateTicketCommand:
	ticket_id: UUID
	title: str
	description: str
	priority: Priority
	created_at: datetime
	application: Application
	assignee_id: UUID | None = None
