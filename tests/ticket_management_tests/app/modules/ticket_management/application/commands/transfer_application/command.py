from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class TransferApplicationCommand:
	ticket_id: UUID
	new_application: Application
	new_assignee: UUID
	transferred_at: datetime
