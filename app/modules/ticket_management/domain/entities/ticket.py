from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.exceptions import (
	DuplicateAttachment,
	EmptyDescription,
	EmptyTitle,
	EmptyComment,
	InvalidAssignee,
	InvalidStatusTransition,
	PendingReasonRequired,
	ResolutionNotesRequired,
	TicketAlreadyAssigned,
	TicketClosed,
	TicketNotAssigned,
)


@dataclass
class Ticket:
	id: UUID
	title: str
	description: str
	status: Status
	priority: Priority
	assignee_id: UUID | None
	created_at: datetime
	updated_at: datetime
	resolved_at: datetime | None = None
	closed_at: datetime | None = None
	pending_reason: str | None = None
	resolution_notes: str | None = None
	comments: list[Comment] = field(default_factory=list)
	attachments: list[Attachment] = field(default_factory=list)

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		title: str,
		description: str,
		priority: Priority,
		created_at: datetime,
		assignee_id: UUID | None = None,
	) -> Ticket:
		if not title.strip():
			raise EmptyTitle()
		if not description.strip():
			raise EmptyDescription()
		if assignee_id is not None and not isinstance(assignee_id, UUID):
			raise InvalidAssignee()
		ticket = cls(
			id=id,
			title=title,
			description=description,
			status=Status.OPEN,
			priority=priority,
			assignee_id=assignee_id,
			created_at=created_at,
			updated_at=created_at,
		)
		return ticket

	def _ensure_not_closed(self) -> None:
		if self.status == Status.CLOSED:
			raise TicketClosed()

	def _transition_to(self, new_status: Status, changed_at: datetime) -> None:
		if self.status == Status.CLOSED:
			raise TicketClosed()

		allowed_transitions = {
			Status.OPEN: {Status.IN_PROGRESS},
			Status.IN_PROGRESS: {Status.PENDING, Status.RESOLVED},
			Status.PENDING: {Status.IN_PROGRESS},
			Status.RESOLVED: {Status.IN_PROGRESS, Status.CLOSED},
			Status.CLOSED: set(),
		}
		if new_status not in allowed_transitions[self.status]:
			raise InvalidStatusTransition()

		self.status = new_status
		self.updated_at = changed_at

	def assign(self, assignee_id: UUID, assigned_at: datetime) -> None:
		self._ensure_not_closed()
		if assignee_id is None:
			raise InvalidAssignee()
		if self.assignee_id is not None:
			raise TicketAlreadyAssigned()
		self.assignee_id = assignee_id
		self.updated_at = assigned_at

	def reassign(self, assignee_id: UUID, reassigned_at: datetime) -> None:
		self._ensure_not_closed()
		if assignee_id is None:
			raise InvalidAssignee()
		if self.assignee_id is None:
			raise TicketNotAssigned()
		self.assignee_id = assignee_id
		self.updated_at = reassigned_at

	def start_progress(self, started_at: datetime) -> None:
		self._transition_to(Status.IN_PROGRESS, started_at)

	def mark_pending(self, reason: str, pending_at: datetime) -> None:
		self._ensure_not_closed()
		if not reason.strip():
			raise PendingReasonRequired()
		self._transition_to(Status.PENDING, pending_at)
		self.pending_reason = reason

	def resume(self, resumed_at: datetime) -> None:
		self._ensure_not_closed()
		if self.status == Status.PENDING:
			self.pending_reason = None
			self._transition_to(Status.IN_PROGRESS, resumed_at)
			return
		if self.status == Status.RESOLVED:
			self._transition_to(Status.IN_PROGRESS, resumed_at)
			self.resolved_at = None
			self.resolution_notes = None
			return
		raise InvalidStatusTransition()

	def resolve(self, notes: str, resolved_at: datetime) -> None:
		self._ensure_not_closed()
		if not notes.strip():
			raise ResolutionNotesRequired()
		self._transition_to(Status.RESOLVED, resolved_at)
		self.resolution_notes = notes
		self.resolved_at = resolved_at
		self.pending_reason = None

	def close(self, closed_at: datetime) -> None:
		self._ensure_not_closed()
		if self.status != Status.RESOLVED:
			raise InvalidStatusTransition()
		self.status = Status.CLOSED
		self.closed_at = closed_at
		self.updated_at = closed_at

	def change_priority(self, priority: Priority, changed_at: datetime) -> None:
		self._ensure_not_closed()
		self.priority = priority
		self.updated_at = changed_at

	def add_comment(self, comment: Comment, added_at: datetime) -> None:
		self._ensure_not_closed()
		if not comment.content.strip():
			raise EmptyComment()
		self.comments.append(comment)
		self.updated_at = added_at

	def add_attachment(self, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_not_closed()
		if any(existing.id == attachment.id for existing in self.attachments):
			raise DuplicateAttachment()
		self.attachments.append(attachment)
		self.updated_at = added_at

