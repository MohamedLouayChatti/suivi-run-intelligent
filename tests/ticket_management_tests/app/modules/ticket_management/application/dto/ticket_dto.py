from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class TicketSummaryDTO:
	id: UUID
	title: str
	application: Application
	status: Status
	priority: Priority
	assignee_id: UUID | None
	created_at: datetime
	updated_at: datetime
	archived_at: datetime | None

	@classmethod
	def from_ticket(cls, ticket: Ticket) -> TicketSummaryDTO:
		return cls(
			id=ticket.id,
			title=ticket.title,
			application=ticket.application,
			status=ticket.status,
			priority=ticket.priority,
			assignee_id=ticket.assignee_id,
			created_at=ticket.created_at,
			updated_at=ticket.updated_at,
			archived_at=ticket.archived_at,
		)


@dataclass(frozen=True)
class TicketDetailDTO:
	id: UUID
	title: str
	description: str
	application: Application
	status: Status
	priority: Priority
	assignee_id: UUID | None
	created_at: datetime
	updated_at: datetime
	resolved_at: datetime | None
	closed_at: datetime | None
	pending_reason: str | None
	resolution_notes: str | None
	comments: list[CommentDTO] = field(default_factory=list)
	attachments: list[AttachmentDTO] = field(default_factory=list)
	archived_at: datetime | None = None

	@classmethod
	def from_ticket(cls, ticket: Ticket) -> TicketDetailDTO:
		return cls(
			id=ticket.id,
			title=ticket.title,
			description=ticket.description,
			application=ticket.application,
			status=ticket.status,
			priority=ticket.priority,
			assignee_id=ticket.assignee_id,
			created_at=ticket.created_at,
			updated_at=ticket.updated_at,
			resolved_at=ticket.resolved_at,
			closed_at=ticket.closed_at,
			pending_reason=ticket.pending_reason,
			resolution_notes=ticket.resolution_notes,
			comments=[CommentDTO.from_comment(comment) for comment in ticket.comments],
			attachments=[AttachmentDTO.from_attachment(attachment) for attachment in ticket.attachments],
			archived_at=ticket.archived_at,
		)
