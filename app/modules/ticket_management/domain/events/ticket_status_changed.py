from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class TicketStatusChanged:
	ticket_id: UUID
	old_status: Status
	new_status: Status
	changed_at: datetime
