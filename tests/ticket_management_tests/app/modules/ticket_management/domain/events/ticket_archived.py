from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TicketArchived:
	ticket_id: UUID
	archived_at: datetime
