from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.exceptions import (
	AttachmentNotFound, CommentNotFound, ConditionalFieldForbidden, DuplicateAttachment,
	ElementRequired, EmptyComment, EmptyDescription, EmptyTitle, InvalidAssignee,
	InvalidStatusTransition, JiraIdRequired, OfferRequired, ResolutionNotesRequired,
	TicketArchived, TicketClosed, TicketNotArchived, TransferDestinationRequired,
	VersionRequired,
)


@dataclass
class Ticket:
	id: UUID
	title: str
	description: str
	application: Application
	status: Status
	priority: Priority
	assignee_id: UUID
	category: Category
	functional_team: FunctionalTeam
	created_at: datetime
	updated_at: datetime
	genergy_id: str | None = None
	oceane_id: str | None = None
	jira_id: str | None = None
	requires_jira: bool = False
	operational_highlight: bool = False
	offer: Offer | None = None
	version: Version | None = None
	element: Element | None = None
	resolved_at: datetime | None = None
	closed_at: datetime | None = None
	resolution_notes: str | None = None
	transferred_to: TransferDestination | None = None
	comments: list[Comment] = field(default_factory=list)
	attachments: list[Attachment] = field(default_factory=list)
	archived_at: datetime | None = None

	@classmethod
	def create(cls, *, id: UUID, title: str, description: str, priority: Priority,
			created_at: datetime, application: Application, assignee_id: UUID,
			category: Category, functional_team: FunctionalTeam,
			genergy_id: str | None = None, oceane_id: str | None = None,
			jira_id: str | None = None, requires_jira: bool = False,
			operational_highlight: bool = False, offer: Offer | None = None,
			version: Version | None = None, element: Element | None = None) -> Ticket:
		if not title.strip():
			raise EmptyTitle()
		if not description.strip():
			raise EmptyDescription()
		if not isinstance(assignee_id, UUID):
			raise InvalidAssignee()
		ticket = cls(id=id, title=title, description=description, application=application,
			status=Status.OPEN, priority=priority, assignee_id=assignee_id,
			category=category, functional_team=functional_team, created_at=created_at,
			updated_at=created_at, genergy_id=genergy_id, oceane_id=oceane_id,
			jira_id=jira_id, requires_jira=requires_jira,
			operational_highlight=operational_highlight, offer=offer, version=version,
			element=element)
		ticket._validate_conditional_fields()
		return ticket

	def _validate_conditional_fields(self) -> None:
		if self.requires_jira and not self.jira_id:
			raise JiraIdRequired()
		if not self.requires_jira and self.jira_id:
			raise ConditionalFieldForbidden()
		if self.application == Application.COLORIS:
			if self.offer is None:
				raise OfferRequired()
			if self.version is None:
				raise VersionRequired()
		elif self.application == Application.AERO:
			if self.element is None:
				raise ElementRequired()
		elif self.offer is not None or self.version is not None or self.element is not None:
			raise ConditionalFieldForbidden()

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
		self._ensure_not_closed()
		allowed = {
			Status.OPEN: {Status.IN_PROGRESS},
			Status.IN_PROGRESS: {Status.RESOLVED, Status.TRANSFERRED},
			Status.TRANSFERRED: {Status.IN_PROGRESS, Status.CLOSED},
			Status.RESOLVED: {Status.IN_PROGRESS, Status.CLOSED},
			Status.CLOSED: set(),
		}
		if new_status not in allowed[self.status]:
			raise InvalidStatusTransition()
		self.status = new_status
		self.updated_at = changed_at

	def reassign(self, assignee_id: UUID, reassigned_at: datetime) -> None:
		self._ensure_mutable()
		if not isinstance(assignee_id, UUID):
			raise InvalidAssignee()
		self.assignee_id = assignee_id
		self.updated_at = reassigned_at

	def start_progress(self, started_at: datetime) -> None:
		self._ensure_mutable()
		self._transition_to(Status.IN_PROGRESS, started_at)

	def resume(self, resumed_at: datetime) -> None:
		self._ensure_mutable()
		if self.status not in {Status.RESOLVED, Status.TRANSFERRED}:
			raise InvalidStatusTransition()
		was_resolved = self.status == Status.RESOLVED
		self._transition_to(Status.IN_PROGRESS, resumed_at)
		if was_resolved:
			self.resolved_at = None
			self.resolution_notes = None
		else:
			self.transferred_to = None

	def resolve(self, notes: str, resolved_at: datetime) -> None:
		self._ensure_mutable()
		if not notes.strip():
			raise ResolutionNotesRequired()
		self._transition_to(Status.RESOLVED, resolved_at)
		self.resolution_notes = notes
		self.resolved_at = resolved_at
		self.transferred_to = None

	def close(self, closed_at: datetime) -> None:
		self._ensure_mutable()
		if self.status not in {Status.RESOLVED, Status.TRANSFERRED}:
			raise InvalidStatusTransition()
		self.status = Status.CLOSED
		self.closed_at = closed_at
		self.updated_at = closed_at

	def transfer(self, destination: TransferDestination, transferred_at: datetime) -> None:
		self._ensure_mutable()
		if destination is None:
			raise TransferDestinationRequired()
		self._transition_to(Status.TRANSFERRED, transferred_at)
		self.transferred_to = destination

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
		self._get_comment(comment_id).edit(content, edited_at)
		self.updated_at = edited_at

	def delete_comment(self, comment_id: UUID, deleted_at: datetime) -> None:
		self._ensure_mutable()
		self._get_comment(comment_id).delete(deleted_at)
		self.updated_at = deleted_at

	def add_attachment_to_comment(self, comment_id: UUID, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_mutable()
		self._get_comment(comment_id).add_attachment(attachment, added_at)
		self.updated_at = added_at

	def delete_attachment_from_comment(self, comment_id: UUID, attachment_id: UUID, deleted_at: datetime) -> None:
		self._ensure_mutable()
		comment = self._get_comment(comment_id)
		attachment = next((item for item in comment.attachments if item.id == attachment_id), None)
		if attachment is None:
			raise AttachmentNotFound()
		attachment.delete(deleted_at)
		self.updated_at = deleted_at