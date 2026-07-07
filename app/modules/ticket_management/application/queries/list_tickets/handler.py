from __future__ import annotations

from app.modules.ticket_management.application.dto.ticket_dto import TicketSummaryDTO
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery


class ListTicketsHandler:
	def __init__(self, read_repository: TicketReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: ListTicketsQuery) -> list[TicketSummaryDTO]:
		return await self.read_repository.list_tickets(query)
