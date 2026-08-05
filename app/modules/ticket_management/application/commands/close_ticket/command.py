from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class CloseTicketCommand:
	ticket_id: UUID
	closed_at: datetime
	actor_id: UUID
