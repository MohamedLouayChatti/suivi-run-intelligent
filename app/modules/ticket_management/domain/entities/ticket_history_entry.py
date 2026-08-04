from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination


@dataclass
class TicketHistoryEntry:
	"""Append-only record of a Ticket lifecycle transition. Entries are never edited or
	deleted — they are produced as a side effect of the Ticket aggregate's own mutating
	methods (create/start_progress/resolve/.../restore), the same way Comment/Attachment
	are appended, so the history can never drift from what actually happened to the ticket."""

	id: UUID
	event_type: TicketHistoryEventType
	occurred_at: datetime
	from_status: Status | None = None
	to_status: Status | None = None
	from_priority: Priority | None = None
	to_priority: Priority | None = None
	assignee_id: UUID | None = None
	transferred_to: TransferDestination | None = None

	@classmethod
	def created(cls, *, id: UUID, occurred_at: datetime) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.CREATED, occurred_at=occurred_at, to_status=Status.OPEN)

	@classmethod
	def status_changed(cls, *, id: UUID, occurred_at: datetime, from_status: Status, to_status: Status) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.STATUS_CHANGED, occurred_at=occurred_at, from_status=from_status, to_status=to_status)

	@classmethod
	def priority_changed(cls, *, id: UUID, occurred_at: datetime, from_priority: Priority, to_priority: Priority) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.PRIORITY_CHANGED, occurred_at=occurred_at, from_priority=from_priority, to_priority=to_priority)

	@classmethod
	def reassigned(cls, *, id: UUID, occurred_at: datetime, assignee_id: UUID) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.REASSIGNED, occurred_at=occurred_at, assignee_id=assignee_id)

	@classmethod
	def transferred(cls, *, id: UUID, occurred_at: datetime, from_status: Status, to_status: Status, transferred_to: TransferDestination) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.TRANSFERRED, occurred_at=occurred_at, from_status=from_status, to_status=to_status, transferred_to=transferred_to)

	@classmethod
	def archived(cls, *, id: UUID, occurred_at: datetime) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.ARCHIVED, occurred_at=occurred_at)

	@classmethod
	def restored(cls, *, id: UUID, occurred_at: datetime) -> TicketHistoryEntry:
		return cls(id=id, event_type=TicketHistoryEventType.RESTORED, occurred_at=occurred_at)
