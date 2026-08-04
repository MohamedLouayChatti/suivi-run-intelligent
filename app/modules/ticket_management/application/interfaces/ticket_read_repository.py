from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery


class TicketReadRepository(ABC):
	@abstractmethod
	async def get_ticket(self, ticket_id: UUID) -> TicketDetailDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_tickets(self, query: ListTicketsQuery) -> list[TicketSummaryDTO]:
		raise NotImplementedError

	@abstractmethod
	async def search_tickets(self, query: SearchTicketsQuery) -> list[TicketSummaryDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket_id_for_comment(self, comment_id: UUID) -> UUID | None:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket_id_for_attachment(self, attachment_id: UUID) -> UUID | None:
		raise NotImplementedError

	@abstractmethod
	async def get_attachment(self, attachment_id: UUID) -> AttachmentDTO | None:
		raise NotImplementedError
