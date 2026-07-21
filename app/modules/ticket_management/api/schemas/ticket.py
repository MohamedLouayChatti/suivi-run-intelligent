from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.ticket_management.api.schemas.attachment import AttachmentResponse
from app.modules.ticket_management.api.schemas.comment import CommentResponse
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


class TicketCreateRequest(BaseModel):
	title: str
	description: str
	priority: Priority
	application: Application
	assignee_id: UUID | None = None


class AssignmentUpdateRequest(BaseModel):
	assignee_id: UUID


class PriorityUpdateRequest(BaseModel):
	priority: Priority


class StatusUpdateRequest(BaseModel):
	status: Status
	pending_reason: str | None = None
	resolution_notes: str | None = None


class ApplicationUpdateRequest(BaseModel):
	application: Application
	assignee_id: UUID


class TicketSummaryResponse(BaseModel):
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
	def from_dto(cls, ticket: TicketSummaryDTO) -> TicketSummaryResponse:
		return cls(**ticket.__dict__)


class TicketDetailResponse(TicketSummaryResponse):
	description: str
	resolved_at: datetime | None
	closed_at: datetime | None
	pending_reason: str | None
	resolution_notes: str | None
	comments: list[CommentResponse]
	attachments: list[AttachmentResponse]

	@classmethod
	def from_dto(cls, ticket: TicketDetailDTO) -> TicketDetailResponse:
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
			comments=[CommentResponse.from_dto(item) for item in ticket.comments],
			attachments=[AttachmentResponse.from_dto(item) for item in ticket.attachments],
			archived_at=ticket.archived_at,
		)
