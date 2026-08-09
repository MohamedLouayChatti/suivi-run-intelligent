from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.ticket_management.api.schemas.attachment import UserSummaryResponse
from app.modules.ticket_management.application.dto.ticket_history_entry_dto import TicketHistoryEntryDTO
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination


class TicketHistoryEntryResponse(BaseModel):
	id: UUID
	event_type: TicketHistoryEventType
	occurred_at: datetime
	from_status: Status | None
	to_status: Status | None
	from_priority: Priority | None
	to_priority: Priority | None
	assignee: UserSummaryResponse | None
	transferred_to: TransferDestination | None
	requires_jira: bool | None
	jira_id: str | None
	jira_delivery_date: date | None
	operational_highlight: bool | None

	@classmethod
	def from_dto(cls, entry: TicketHistoryEntryDTO) -> TicketHistoryEntryResponse:
		return cls(
			id=entry.id,
			event_type=entry.event_type,
			occurred_at=entry.occurred_at,
			from_status=entry.from_status,
			to_status=entry.to_status,
			from_priority=entry.from_priority,
			to_priority=entry.to_priority,
			assignee=UserSummaryResponse.from_dto(entry.assignee),
			transferred_to=entry.transferred_to,
			requires_jira=entry.requires_jira,
			jira_id=entry.jira_id,
			jira_delivery_date=entry.jira_delivery_date,
			operational_highlight=entry.operational_highlight,
		)
