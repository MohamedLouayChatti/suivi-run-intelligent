from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RestoreTicketCommand:
	ticket_id: UUID
	restored_at: datetime
