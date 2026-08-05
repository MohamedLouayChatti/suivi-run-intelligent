from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class ResolveTicketCommand:
	ticket_id: UUID
	resolution_notes: str
	resolved_at: datetime
	actor_id: UUID
