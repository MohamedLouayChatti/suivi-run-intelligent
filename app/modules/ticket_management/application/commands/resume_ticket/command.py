from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class ResumeTicketCommand:
	ticket_id: UUID
	resumed_at: datetime
	actor_id: UUID
