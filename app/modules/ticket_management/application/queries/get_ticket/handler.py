from __future__ import annotations

from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.queries.user_enricher import TicketUserEnricher


class GetTicketHandler:
	def __init__(self, read_repository: TicketReadRepository, user_repository: UserReadRepository | None = None) -> None:
		self.read_repository = read_repository
		self.user_enricher = None if user_repository is None else TicketUserEnricher(user_repository)

	async def handle(self, query: GetTicketQuery) -> TicketDetailDTO:
		ticket = await self.read_repository.get_ticket(query.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		return ticket if self.user_enricher is None else await self.user_enricher.detail(ticket)
