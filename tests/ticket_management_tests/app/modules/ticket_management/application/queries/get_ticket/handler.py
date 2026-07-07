from __future__ import annotations

from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO


class GetTicketHandler:
	def __init__(self, read_repository: TicketReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetTicketQuery) -> TicketDetailDTO:
		ticket = await self.read_repository.get_ticket(query.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		return ticket
