from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType


@dataclass(frozen=True)
class TicketLifecycleEventDTO:
	"""One CREATED/STATUS_CHANGED/ARCHIVED/RESTORED history entry -- the projection
	`reconstruct_daily_active_counts` replays to determine whether a ticket was active on a
	given day."""

	ticket_id: UUID
	occurred_at: datetime
	event_type: TicketHistoryEventType
	to_status: Status | None
