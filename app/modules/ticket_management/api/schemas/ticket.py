from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.ticket_management.api.schemas.attachment import AttachmentResponse
from app.modules.ticket_management.api.schemas.comment import CommentResponse
from app.modules.ticket_management.api.schemas.history import TicketHistoryEntryResponse
from app.modules.ticket_management.api.schemas.attachment import UserSummaryResponse
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.enums.version import Version
from app.modules.ticket_management.domain.enums.vio_app import VioApp


class TicketCreateRequest(BaseModel):
	title: str
	description: str
	priority: Priority
	application: Application
	category: Category
	functional_team: FunctionalTeam
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


class ReassignRequest(BaseModel):
	assignee_id: UUID


class PriorityUpdateRequest(BaseModel):
	priority: Priority


class ResolveRequest(BaseModel):
	resolution_notes: str


class TransferRequest(BaseModel):
	transferred_to: TransferDestination


class TicketSummaryResponse(BaseModel):
	id: UUID
	title: str
	application: Application
	status: Status
	priority: Priority
	assignee: UserSummaryResponse | None
	category: Category
	functional_team: FunctionalTeam
	operational_highlight: bool
	transferred_to: TransferDestination | None
	created_at: datetime
	updated_at: datetime
	archived_at: datetime | None

	@classmethod
	def from_dto(cls, ticket: TicketSummaryDTO) -> TicketSummaryResponse:
		return cls(
			id=ticket.id, title=ticket.title, application=ticket.application, status=ticket.status,
			priority=ticket.priority, assignee=UserSummaryResponse.from_dto(ticket.assignee),
			category=ticket.category, functional_team=ticket.functional_team,
			operational_highlight=ticket.operational_highlight, transferred_to=ticket.transferred_to,
			created_at=ticket.created_at, updated_at=ticket.updated_at, archived_at=ticket.archived_at,
		)


class TicketDetailResponse(TicketSummaryResponse):
	description: str
	resolved_at: datetime | None
	closed_at: datetime | None
	genergy_id: str | None
	oceane_id: str | None
	jira_id: str | None
	jira_delivery_date: date | None
	requires_jira: bool
	operational_highlight: bool
	offer: Offer | None
	version: Version | None
	element: Element | None
	vio_app: VioApp | None
	transferred_to: TransferDestination | None
	resolution_notes: str | None
	comments: list[CommentResponse]
	attachments: list[AttachmentResponse]
	history: list[TicketHistoryEntryResponse]

	@classmethod
	def from_dto(cls, ticket: TicketDetailDTO) -> TicketDetailResponse:
		return cls(
			id=ticket.id,
			title=ticket.title,
			description=ticket.description,
			application=ticket.application,
			status=ticket.status,
			priority=ticket.priority,
			assignee=UserSummaryResponse.from_dto(ticket.assignee),
			created_at=ticket.created_at,
			updated_at=ticket.updated_at,
			resolved_at=ticket.resolved_at,
			closed_at=ticket.closed_at,
			category=ticket.category,
			functional_team=ticket.functional_team,
			genergy_id=ticket.genergy_id,
			oceane_id=ticket.oceane_id,
			jira_id=ticket.jira_id,
			jira_delivery_date=ticket.jira_delivery_date,
			requires_jira=ticket.requires_jira,
			operational_highlight=ticket.operational_highlight,
			offer=ticket.offer,
			version=ticket.version,
			element=ticket.element,
			vio_app=ticket.vio_app,
			transferred_to=ticket.transferred_to,
			resolution_notes=ticket.resolution_notes,
			comments=[CommentResponse.from_dto(item) for item in ticket.comments],
			attachments=[AttachmentResponse.from_dto(item) for item in ticket.attachments],
			history=[TicketHistoryEntryResponse.from_dto(item) for item in ticket.history],
			archived_at=ticket.archived_at,
		)
