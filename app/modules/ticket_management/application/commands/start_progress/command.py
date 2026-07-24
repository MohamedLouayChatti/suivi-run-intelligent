from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class StartProgressCommand:
	ticket_id: UUID
	started_at: datetime
