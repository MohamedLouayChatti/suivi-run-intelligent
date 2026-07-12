"""
Plain factory functions for the read-side DTOs (`TicketSummaryDTO`,
`TicketDetailDTO`). Kept separate from the domain factories since these
are application-layer read models, not domain entities — a query handler
test shouldn't need to build a full `Ticket` aggregate (with all its
invariants) just to hand the fake read repository something to return.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from tests.unit.ticket_management.domain import factories as domain_factories

BASE_TIME = domain_factories.BASE_TIME


def make_summary_dto(
	*,
	id: UUID | None = None,
	title: str = "Payment gateway returns 500",
	application: Application = Application.APP_1,
	status: Status = Status.OPEN,
	priority: Priority = Priority.MEDIUM,
	assignee_id: UUID | None = None,
	created_at: datetime = BASE_TIME,
	updated_at: datetime = BASE_TIME,
	archived_at: datetime | None = None,
) -> TicketSummaryDTO:
	return TicketSummaryDTO(
		id=id or domain_factories.new_uuid(),
		title=title,
		application=application,
		status=status,
		priority=priority,
		assignee_id=assignee_id,
		created_at=created_at,
		updated_at=updated_at,
		archived_at=archived_at,
	)


def make_detail_dto(
	*,
	id: UUID | None = None,
	title: str = "Payment gateway returns 500",
	description: str = "Customers report failed checkouts since the last deploy.",
	application: Application = Application.APP_1,
	status: Status = Status.OPEN,
	priority: Priority = Priority.MEDIUM,
	assignee_id: UUID | None = None,
	created_at: datetime = BASE_TIME,
	updated_at: datetime = BASE_TIME,
	resolved_at: datetime | None = None,
	closed_at: datetime | None = None,
	pending_reason: str | None = None,
	resolution_notes: str | None = None,
	comments: list[CommentDTO] | None = None,
	attachments: list[AttachmentDTO] | None = None,
	archived_at: datetime | None = None,
) -> TicketDetailDTO:
	return TicketDetailDTO(
		id=id or domain_factories.new_uuid(),
		title=title,
		description=description,
		application=application,
		status=status,
		priority=priority,
		assignee_id=assignee_id,
		created_at=created_at,
		updated_at=updated_at,
		resolved_at=resolved_at,
		closed_at=closed_at,
		pending_reason=pending_reason,
		resolution_notes=resolution_notes,
		comments=comments or [],
		attachments=attachments or [],
		archived_at=archived_at,
	)
