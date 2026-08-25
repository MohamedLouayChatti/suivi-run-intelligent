from __future__ import annotations

from app.modules.knowledge_base.application.dto.similar_incident_dto import SimilarIncidentDTO
from app.modules.knowledge_base.application.interfaces.similarity_read_repository import SimilarityReadRepository
from app.modules.knowledge_base.application.queries.get_similar_incidents.query import GetSimilarIncidentsQuery
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository


class GetSimilarIncidentsHandler:
	"""Backs GET /knowledge-base/tickets/{ticket_id}/similar. Plain DB read of
	already-persisted SimilarityResult rows, enriched with live title/status/resolution_notes via
	Ticket Management's TicketReadRepository -- never triggers embedding or vector search.
	"""

	def __init__(self, similarity_read_repository: SimilarityReadRepository, ticket_read_repository: TicketReadRepository) -> None:
		self.similarity_read_repository = similarity_read_repository
		self.ticket_read_repository = ticket_read_repository

	async def handle(self, query: GetSimilarIncidentsQuery) -> list[SimilarIncidentDTO]:
		rows = await self.similarity_read_repository.get_for_source(query.ticket_id)
		if not rows:
			return []

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
		return results
