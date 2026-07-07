from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TicketAssigned:
	ticket_id: UUID
	assignee_id: UUID
	assigned_at: datetime
