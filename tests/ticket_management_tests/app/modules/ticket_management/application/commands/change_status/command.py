from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class ChangeStatusCommand:
	ticket_id: UUID
	status: Status
	changed_at: datetime
	pending_reason: str | None = None
	resolution_notes: str | None = None
