from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class TicketTransferred:
	ticket_id: UUID
	old_application: Application
	new_application: Application
	old_assignee_id: UUID | None
	new_assignee_id: UUID
	transferred_at: datetime
