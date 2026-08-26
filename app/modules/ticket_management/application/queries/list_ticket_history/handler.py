from __future__ import annotations

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.list_ticket_history.query import ListTicketHistoryQuery
from app.modules.ticket_management.application.queries.user_enricher import TicketUserEnricher
from app.modules.ticket_management.application.dto.ticket_dto import TicketSummaryDTO
from app.shared.pagination import Page


class ListTicketHistoryHandler:
	def __init__(self, read_repository: TicketReadRepository, user_repository: UserReadRepository | None = None) -> None:
		self.read_repository = read_repository
		self.user_enricher = None if user_repository is None else TicketUserEnricher(user_repository)

	async def handle(self, query: ListTicketHistoryQuery) -> Page[TicketSummaryDTO]:
		items = await self.read_repository.list_history(query)
		total = await self.read_repository.count_history(query)
		if self.user_enricher is not None:
			items = await self.user_enricher.summaries(items)
		return Page(items=items, total=total)
