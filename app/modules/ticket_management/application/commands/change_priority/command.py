from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.priority import Priority


@dataclass(frozen=True)
class ChangePriorityCommand:
	ticket_id: UUID
	priority: Priority
	changed_at: datetime
