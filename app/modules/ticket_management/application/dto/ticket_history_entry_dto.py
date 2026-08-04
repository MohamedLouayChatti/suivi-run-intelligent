from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.ticket_management.domain.entities.ticket_history_entry import TicketHistoryEntry
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination


@dataclass(frozen=True)
class TicketHistoryEntryDTO:
	id: UUID
	event_type: TicketHistoryEventType
	occurred_at: datetime
	from_status: Status | None = None
	to_status: Status | None = None
	from_priority: Priority | None = None
	to_priority: Priority | None = None
	assignee_id: UUID | None = None
	transferred_to: TransferDestination | None = None
	assignee: UserSummaryDTO | None = None

	@classmethod
	def from_history_entry(cls, entry: TicketHistoryEntry) -> TicketHistoryEntryDTO:
		return cls(
			id=entry.id,
			event_type=entry.event_type,
			occurred_at=entry.occurred_at,
			from_status=entry.from_status,
			to_status=entry.to_status,
			from_priority=entry.from_priority,
			to_priority=entry.to_priority,
			assignee_id=entry.assignee_id,
			transferred_to=entry.transferred_to,
		)
