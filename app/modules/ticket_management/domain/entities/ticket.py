from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.entities.ticket_history_entry import TicketHistoryEntry
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.enums.vio_app import VioApp
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.exceptions import (
	AssigneeUnchanged, AttachmentNotFound, ChronologicalOrderViolation, CommentNotFound, ConditionalFieldForbidden,
	DuplicateAttachment, ElementRequired, EmptyComment, EmptyDescription, EmptyTitle,
	InvalidAssignee, InvalidStatusTransition, JiraIdRequired, OfferRequired,
	ResolutionNotesRequired, TicketArchived, TicketClosed, TicketNotArchived,
	TransferDestinationIsOrigin, TransferDestinationRequired, VersionRequired, VioAppRequired,
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
	jira_delivery_date: date | None = None
	requires_jira: bool = False
	operational_highlight: bool = False
	offer: Offer | None = None
	version: Version | None = None
	element: Element | None = None
	vio_app: VioApp | None = None
	resolved_at: datetime | None = None
	closed_at: datetime | None = None
	resolution_notes: str | None = None
	transferred_to: TransferDestination | None = None
	comments: list[Comment] = field(default_factory=list)
	attachments: list[Attachment] = field(default_factory=list)
	history: list[TicketHistoryEntry] = field(default_factory=list)
	archived_at: datetime | None = None

	@classmethod
	def create(cls, *, id: UUID, title: str, description: str, priority: Priority,
			created_at: datetime, application: Application, assignee_id: UUID,
			category: Category, functional_team: FunctionalTeam,
			genergy_id: str | None = None, oceane_id: str | None = None,
			jira_id: str | None = None, requires_jira: bool = False,
			operational_highlight: bool = False, offer: Offer | None = None,
			version: Version | None = None, element: Element | None = None,
			jira_delivery_date: date | None = None,
			vio_app: VioApp | None = None) -> Ticket:
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
			element=element, jira_delivery_date=jira_delivery_date, vio_app=vio_app)
		ticket._validate_conditional_fields()
		ticket.history.append(TicketHistoryEntry.created(id=uuid4(), occurred_at=created_at))
		return ticket

	def _validate_conditional_fields(self) -> None:
		if self.requires_jira and not self.jira_id:
			raise JiraIdRequired()
		if not self.requires_jira and self.jira_id:
			raise ConditionalFieldForbidden()
		if self.jira_id is None and self.jira_delivery_date is not None:
			raise ConditionalFieldForbidden()
		if self.application == Application.COLORIS:
			if self.offer is None:
				raise OfferRequired()
			if self.version is None:
				raise VersionRequired()
			if self.element is not None or self.vio_app is not None:
				raise ConditionalFieldForbidden()
		elif self.application == Application.AERO:
			if self.element is None:
				raise ElementRequired()
			if self.offer is not None or self.version is not None or self.vio_app is not None:
				raise ConditionalFieldForbidden()
		elif self.application == Application.VIO:
			if self.vio_app is None:
				raise VioAppRequired()
			if self.offer is not None or self.version is not None or self.element is not None:
				raise ConditionalFieldForbidden()
		elif self.offer is not None or self.version is not None or self.element is not None or self.vio_app is not None:
			raise ConditionalFieldForbidden()

	def _ensure_not_closed(self) -> None:
		if self.status == Status.CLOSED:
			raise TicketClosed()

	def _ensure_not_archived(self) -> None:
		if self.archived_at is not None:
			raise TicketArchived()

	def _ensure_chronological(self, at: datetime) -> None:
		if at < self.updated_at:
			raise ChronologicalOrderViolation()

	def _ensure_mutable(self, at: datetime) -> None:
		self._ensure_not_closed()
		self._ensure_not_archived()
		self._ensure_chronological(at)

	def archive(self, archived_at: datetime) -> None:
		self._ensure_not_archived()
		self._ensure_chronological(archived_at)
		self.archived_at = archived_at
		self.updated_at = archived_at
		self.history.append(TicketHistoryEntry.archived(id=uuid4(), occurred_at=archived_at))

	def restore(self, restored_at: datetime) -> None:
		if self.archived_at is None:
			raise TicketNotArchived()
		self._ensure_chronological(restored_at)
		self.archived_at = None
		self.updated_at = restored_at
		self.history.append(TicketHistoryEntry.restored(id=uuid4(), occurred_at=restored_at))

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
		self._ensure_mutable(reassigned_at)
		if not isinstance(assignee_id, UUID):
			raise InvalidAssignee()
		if assignee_id == self.assignee_id:
			raise AssigneeUnchanged()
		self.assignee_id = assignee_id
		self.updated_at = reassigned_at
		self.history.append(TicketHistoryEntry.reassigned(id=uuid4(), occurred_at=reassigned_at, assignee_id=assignee_id))

	def start_progress(self, started_at: datetime) -> None:
		self._ensure_mutable(started_at)
		old_status = self.status
		self._transition_to(Status.IN_PROGRESS, started_at)
		self.history.append(TicketHistoryEntry.status_changed(id=uuid4(), occurred_at=started_at, from_status=old_status, to_status=self.status))

	def resume(self, resumed_at: datetime) -> None:
		self._ensure_mutable(resumed_at)
		if self.status not in {Status.RESOLVED, Status.TRANSFERRED}:
			raise InvalidStatusTransition()
		old_status = self.status
		was_resolved = self.status == Status.RESOLVED
		self._transition_to(Status.IN_PROGRESS, resumed_at)
		if was_resolved:
			self.resolved_at = None
			self.resolution_notes = None
		else:
			self.transferred_to = None
		self.history.append(TicketHistoryEntry.status_changed(id=uuid4(), occurred_at=resumed_at, from_status=old_status, to_status=self.status))

	def resolve(self, notes: str, resolved_at: datetime) -> None:
		self._ensure_mutable(resolved_at)
		if not notes.strip():
			raise ResolutionNotesRequired()
		old_status = self.status
		self._transition_to(Status.RESOLVED, resolved_at)
		self.resolution_notes = notes
		self.resolved_at = resolved_at
		self.transferred_to = None
		self.history.append(TicketHistoryEntry.status_changed(id=uuid4(), occurred_at=resolved_at, from_status=old_status, to_status=self.status))

	def close(self, closed_at: datetime) -> None:
		self._ensure_mutable(closed_at)
		if self.status not in {Status.RESOLVED, Status.TRANSFERRED}:
			raise InvalidStatusTransition()
		old_status = self.status
		self.status = Status.CLOSED
		self.closed_at = closed_at
		self.updated_at = closed_at
		self.history.append(TicketHistoryEntry.status_changed(id=uuid4(), occurred_at=closed_at, from_status=old_status, to_status=self.status))

	def transfer(self, destination: TransferDestination, transferred_at: datetime) -> None:
		self._ensure_mutable(transferred_at)
		if destination is None:
			raise TransferDestinationRequired()
		if destination.is_origin_of(self.functional_team, self.application):
			raise TransferDestinationIsOrigin()
		old_status = self.status
		self._transition_to(Status.TRANSFERRED, transferred_at)
		self.transferred_to = destination
		self.history.append(TicketHistoryEntry.transferred(id=uuid4(), occurred_at=transferred_at, from_status=old_status, to_status=self.status, transferred_to=destination))

	def change_priority(self, priority: Priority, changed_at: datetime) -> None:
		self._ensure_mutable(changed_at)
		old_priority = self.priority
		self.priority = priority
		self.updated_at = changed_at
		self.history.append(TicketHistoryEntry.priority_changed(id=uuid4(), occurred_at=changed_at, from_priority=old_priority, to_priority=priority))

	def update_jira_details(self, *, requires_jira: bool, jira_id: str | None, jira_delivery_date: date | None, updated_at: datetime) -> None:
		self._ensure_mutable(updated_at)
		if not requires_jira:
			jira_id = None
			jira_delivery_date = None
		elif not jira_id:
			raise JiraIdRequired()
		if jira_id is None and jira_delivery_date is not None:
			raise ConditionalFieldForbidden()
		self.requires_jira = requires_jira
		self.jira_id = jira_id
		self.jira_delivery_date = jira_delivery_date
		self.updated_at = updated_at
		self.history.append(TicketHistoryEntry.jira_updated(id=uuid4(), occurred_at=updated_at, requires_jira=requires_jira, jira_id=jira_id, jira_delivery_date=jira_delivery_date))

	def set_operational_highlight(self, operational_highlight: bool, updated_at: datetime) -> None:
		self._ensure_mutable(updated_at)
		self.operational_highlight = operational_highlight
		self.updated_at = updated_at
		self.history.append(TicketHistoryEntry.operational_highlight_changed(id=uuid4(), occurred_at=updated_at, operational_highlight=operational_highlight))

	def add_comment(self, comment: Comment, added_at: datetime) -> None:
		self._ensure_mutable(added_at)
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
		self._ensure_mutable(added_at)
		if any(existing.id == attachment.id for existing in self.attachments):
			raise DuplicateAttachment()
		self.attachments.append(attachment)
		self.updated_at = added_at

	def edit_comment(self, comment_id: UUID, content: str, edited_at: datetime) -> None:
		self._ensure_mutable(edited_at)
		self._get_comment(comment_id).edit(content, edited_at)
		self.updated_at = edited_at

	def delete_comment(self, comment_id: UUID, deleted_at: datetime) -> None:
		self._ensure_mutable(deleted_at)
		self._get_comment(comment_id).delete(deleted_at)
		self.updated_at = deleted_at

	def add_attachment_to_comment(self, comment_id: UUID, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_mutable(added_at)
		self._get_comment(comment_id).add_attachment(attachment, added_at)
		self.updated_at = added_at

	def delete_attachment_from_comment(self, comment_id: UUID, attachment_id: UUID, deleted_at: datetime) -> None:
		self._ensure_mutable(deleted_at)
		comment = self._get_comment(comment_id)
		attachment = next((item for item in comment.attachments if item.id == attachment_id), None)
		if attachment is None:
			raise AttachmentNotFound()
		attachment.delete(deleted_at)
		self.updated_at = deleted_at
