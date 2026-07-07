from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.priority import Priority


@dataclass(frozen=True)
class PriorityChanged:
	ticket_id: UUID
	old_priority: Priority
	new_priority: Priority
	changed_at: datetime
