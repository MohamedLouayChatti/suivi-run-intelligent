from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.exceptions import (
	AttachmentNotFound,
	CommentNotFound,
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
	SameApplicationTransfer,
	TicketArchived,
	TicketNotArchived,
)


@dataclass
class Ticket:
	id: UUID
	title: str
	description: str
	application: Application
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
	archived_at: datetime | None = None

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		title: str,
		description: str,
		priority: Priority,
		created_at: datetime,
		application: Application,
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
			application=application,
			status=Status.OPEN,
			priority=priority,
			assignee_id=assignee_id,
			created_at=created_at,
			updated_at=created_at,
			archived_at=None
		)
		return ticket

	def _ensure_not_closed(self) -> None:
		if self.status == Status.CLOSED:
			raise TicketClosed()
		
	def _ensure_not_archived(self) -> None:
		if self.archived_at is not None:
			raise TicketArchived()
		
	def _ensure_mutable(self) -> None:
		self._ensure_not_closed()
		self._ensure_not_archived()
		
	def archive(self, archived_at: datetime) -> None:
		self._ensure_not_archived()
		self.archived_at = archived_at
		self.updated_at = archived_at

	def restore(self, restored_at: datetime) -> None:
		if self.archived_at is None:
			raise TicketNotArchived()
		self.archived_at = None
		self.updated_at = restored_at

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
		self._ensure_mutable()
		if assignee_id is None:
			raise InvalidAssignee()
		if self.assignee_id is not None:
			raise TicketAlreadyAssigned()
		self.assignee_id = assignee_id
		self.updated_at = assigned_at

	def reassign(self, assignee_id: UUID, reassigned_at: datetime) -> None:
		self._ensure_mutable()
		if assignee_id is None:
			raise InvalidAssignee()
		if self.assignee_id is None:
			raise TicketNotAssigned()
		self.assignee_id = assignee_id
		self.updated_at = reassigned_at

	def start_progress(self, started_at: datetime) -> None:
		self._transition_to(Status.IN_PROGRESS, started_at)

	def mark_pending(self, reason: str, pending_at: datetime) -> None:
		self._ensure_mutable()
		if not reason.strip():
			raise PendingReasonRequired()
		self._transition_to(Status.PENDING, pending_at)
		self.pending_reason = reason

	def resume(self, resumed_at: datetime) -> None:
		self._ensure_mutable()
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
		self._ensure_mutable()
		if not notes.strip():
			raise ResolutionNotesRequired()
		self._transition_to(Status.RESOLVED, resolved_at)
		self.resolution_notes = notes
		self.resolved_at = resolved_at
		self.pending_reason = None

	def close(self, closed_at: datetime) -> None:
		self._ensure_mutable()
		if self.status != Status.RESOLVED:
			raise InvalidStatusTransition()
		self.status = Status.CLOSED
		self.closed_at = closed_at
		self.updated_at = closed_at

	def change_priority(self, priority: Priority, changed_at: datetime) -> None:
		self._ensure_mutable()
		self.priority = priority
		self.updated_at = changed_at

	def add_comment(self, comment: Comment, added_at: datetime) -> None:
		self._ensure_mutable()
		if not comment.content.strip():
			raise EmptyComment()
		self.comments.append(comment)
		self.updated_at = added_at

	def _get_comment(self, comment_id: UUID) -> Comment:
		comment = next((item for item in self.comments if item.id == comment_id), None)
		if comment is None:
			raise CommentNotFound()
		return comment

	def add_attachment(self, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_mutable()
		if any(existing.id == attachment.id for existing in self.attachments):
			raise DuplicateAttachment()
		self.attachments.append(attachment)
		self.updated_at = added_at

	def edit_comment(self, comment_id: UUID, content: str, edited_at: datetime) -> None:
		self._ensure_mutable()
		comment = self._get_comment(comment_id)
		comment.edit(content, edited_at)
		self.updated_at = edited_at

	def delete_comment(self, comment_id: UUID, deleted_at: datetime) -> None:
		self._ensure_mutable()
		comment = self._get_comment(comment_id)
		comment.delete(deleted_at)
		self.updated_at = deleted_at

	def add_attachment_to_comment(self, comment_id: UUID, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_mutable()
		comment = self._get_comment(comment_id)
		comment.add_attachment(attachment, added_at)
		self.updated_at = added_at

	def delete_attachment_from_comment(self, comment_id: UUID, attachment_id: UUID, deleted_at: datetime) -> None:
		self._ensure_mutable()
		comment = self._get_comment(comment_id)
		attachment = next((item for item in comment.attachments if item.id == attachment_id), None)
		if attachment is None:
			raise AttachmentNotFound()
		attachment.delete(deleted_at)
		self.updated_at = deleted_at

	def transfer_application(self, new_application: Application, new_assignee: UUID, transferred_at: datetime) -> None:
		self._ensure_mutable()

		if self.application == new_application:
			raise SameApplicationTransfer()
		if new_assignee is None:
			raise InvalidAssignee()
		if self.assignee_id is None:
			raise TicketNotAssigned()

		self.application = new_application
		self.assignee_id = new_assignee
		self.updated_at = transferred_at