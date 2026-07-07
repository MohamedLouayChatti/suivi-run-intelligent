from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TicketReassigned:
	ticket_id: UUID
	assignee_id: UUID
	reassigned_at: datetime
