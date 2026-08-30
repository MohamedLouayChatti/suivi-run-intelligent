from __future__ import annotations

from app.modules.knowledge_base.application.dto.similar_incident_dto import (
	SimilarIncidentDTO,
	SimilarIncidentsDTO,
	SimilarityAnalysisStatus,
)
from app.modules.knowledge_base.application.interfaces.similarity_read_repository import SimilarityReadRepository
from app.modules.knowledge_base.application.queries.get_similar_incidents.query import GetSimilarIncidentsQuery
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository


class GetSimilarIncidentsHandler:
	"""Backs GET /knowledge-base/tickets/{ticket_id}/similar. Plain DB read of
	already-persisted SimilarityResult rows, enriched with live title/status/resolution_notes via
	Ticket Management's TicketReadRepository -- never triggers embedding or vector search.

	It also answers whether the analysis has run at all, because since a new ticket is analysed in a
	background job the caller can now arrive before it has. The corpus is what is asked: generation
	writes the ticket's knowledge item and then its results, so a ticket the corpus does not hold is
	one nothing has looked at yet. Deliberately not a stored flag -- that would be a second source of
	truth about a fact the corpus already answers, and one more thing to keep in step with it.

	Only consulted when there are no rows. Rows are unambiguous on their own, so the common case
	still costs exactly the reads it did before, and the extra round trip is paid only in the case
	that needs disambiguating.
	"""

	def __init__(
		self,
		similarity_read_repository: SimilarityReadRepository,
		ticket_read_repository: TicketReadRepository,
		knowledge_items: KnowledgeItemRepository,
	) -> None:
		self.similarity_read_repository = similarity_read_repository
		self.ticket_read_repository = ticket_read_repository
		self.knowledge_items = knowledge_items

	async def handle(self, query: GetSimilarIncidentsQuery) -> SimilarIncidentsDTO:
		rows = await self.similarity_read_repository.get_for_source(query.ticket_id)
		if not rows:
			# The two stores have no transaction between them, so this can read READY during the
			# sub-second gap between generation's corpus write and its results commit, and report a
			# genuine "no match" a moment early. The narrower reading -- a ticket in the corpus with
			# no results row -- is a state this module already treats as legitimate and the rebuild
			# pass repairs; erring the other way would leave a ticket that really has no match
			# reported as pending forever.
			analysed = await self.knowledge_items.exists(query.ticket_id)
			return SimilarIncidentsDTO(
				status=SimilarityAnalysisStatus.READY if analysed else SimilarityAnalysisStatus.PENDING,
				incidents=[],
			)

		summaries = await self.ticket_read_repository.get_similarity_summaries(
			[row.similar_ticket_id for row in rows]
		)
		summaries_by_id = {summary.id: summary for summary in summaries}

		results = []
		for row in rows:
			summary = summaries_by_id.get(row.similar_ticket_id)
			if summary is None:
				continue
			results.append(
				SimilarIncidentDTO(
					ticket_id=row.similar_ticket_id, title=summary.title, status=summary.status,
					resolution_notes=summary.resolution_notes,
					similarity_score=row.similarity_score, rank=row.rank,
					matched_reference=row.matched_reference,
				)
			)
		return SimilarIncidentsDTO(status=SimilarityAnalysisStatus.READY, incidents=results)
