from __future__ import annotations

from app.modules.ticket_management.application.dto.ticket_dto import TicketSummaryDTO
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.queries.user_enricher import TicketUserEnricher


class SearchTicketsHandler:
	def __init__(self, read_repository: TicketReadRepository, user_repository: UserReadRepository | None = None) -> None:
		self.read_repository = read_repository
		self.user_enricher = None if user_repository is None else TicketUserEnricher(user_repository)

	async def handle(self, query: SearchTicketsQuery) -> list[TicketSummaryDTO]:
		result = await self.read_repository.search_tickets(query)
		return result if self.user_enricher is None else await self.user_enricher.summaries(result)
