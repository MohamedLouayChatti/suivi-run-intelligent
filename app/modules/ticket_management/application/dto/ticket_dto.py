from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO
from app.modules.ticket_management.application.dto.ticket_history_entry_dto import TicketHistoryEntryDTO
from app.modules.ticket_management.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.ticket_management.domain.entities.ticket import Ticket
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


@dataclass(frozen=True)
class TicketSummaryDTO:
	id: UUID; title: str; application: Application; status: Status; priority: Priority
	assignee_id: UUID; category: Category; functional_team: FunctionalTeam
	operational_highlight: bool; transferred_to: TransferDestination | None
	created_at: datetime; updated_at: datetime; archived_at: datetime | None
	assignee: UserSummaryDTO | None = None

	@classmethod
	def from_ticket(cls, ticket: Ticket) -> TicketSummaryDTO:
		return cls(ticket.id, ticket.title, ticket.application, ticket.status, ticket.priority,
			ticket.assignee_id, ticket.category, ticket.functional_team, ticket.operational_highlight,
			ticket.transferred_to, ticket.created_at, ticket.updated_at, ticket.archived_at)


@dataclass(frozen=True)
class TicketSimilaritySummaryDTO:
	"""Narrow projection for Knowledge Base to enrich SimilarityResult rows with live ticket
	context (title/status/resolution_notes) without depending on TicketDetailDTO's full shape.

	resolution_notes is not cached anywhere in Knowledge Base -- it's fetched fresh through this
	DTO on every read, because Ticket.resume() clears it, so a cached copy could go stale the
	moment a resolved ticket reopens.
	"""

	id: UUID
	title: str
	status: Status
	resolution_notes: str | None

	@classmethod
	def from_ticket(cls, ticket: Ticket) -> TicketSimilaritySummaryDTO:
		return cls(ticket.id, ticket.title, ticket.status, ticket.resolution_notes)


@dataclass(frozen=True)
class TicketContentDTO:
	"""The textual content of a ticket plus the metadata needed to scope and cross-reference it.

	Deliberately narrower than TicketDetailDTO and deliberately named for what it *is* rather than
	for what any consumer does with it: the whole point of this module owning no knowledge of
	downstream processing is that a projection of ticket text must not be called, say, an
	embedding source. Nothing here is specific to any consumer -- it is id, scope, text, and the
	two external identifiers.

	Paged over rather than fetched whole because the caller is a bulk pass over every ticket ever
	created, which must not have to hold the entire corpus in memory to run.
	"""

	id: UUID
	application: Application
	description: str
	genergy_id: str | None
	oceane_id: str | None


@dataclass(frozen=True)
class TicketDetailDTO:
	id: UUID; title: str; description: str; application: Application; status: Status; priority: Priority
	assignee_id: UUID; category: Category; functional_team: FunctionalTeam
	genergy_id: str | None; oceane_id: str | None; jira_id: str | None; jira_delivery_date: date | None; requires_jira: bool
	operational_highlight: bool; offer: Offer | None; version: Version | None; element: Element | None; vio_app: VioApp | None
	transferred_to: TransferDestination | None; created_at: datetime; updated_at: datetime
	resolved_at: datetime | None; closed_at: datetime | None; resolution_notes: str | None
	comments: list[CommentDTO] = field(default_factory=list)
	attachments: list[AttachmentDTO] = field(default_factory=list)
	history: list[TicketHistoryEntryDTO] = field(default_factory=list)
	archived_at: datetime | None = None
	assignee: UserSummaryDTO | None = None

	@classmethod
	def from_ticket(cls, ticket: Ticket) -> TicketDetailDTO:
		return cls(ticket.id, ticket.title, ticket.description, ticket.application, ticket.status,
			ticket.priority, ticket.assignee_id, ticket.category, ticket.functional_team,
			ticket.genergy_id, ticket.oceane_id, ticket.jira_id, ticket.jira_delivery_date, ticket.requires_jira,
			ticket.operational_highlight, ticket.offer, ticket.version, ticket.element, ticket.vio_app,
			ticket.transferred_to, ticket.created_at, ticket.updated_at, ticket.resolved_at,
			ticket.closed_at, ticket.resolution_notes,
			[CommentDTO.from_comment(c) for c in ticket.comments],
			[AttachmentDTO.from_attachment(a) for a in ticket.attachments],
			[TicketHistoryEntryDTO.from_history_entry(h) for h in ticket.history],
			ticket.archived_at)
