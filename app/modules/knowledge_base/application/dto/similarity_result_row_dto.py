from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SimilarityResultRowDTO:
	"""Raw persisted SimilarityResult projection -- KB-owned fields only, no ticket content.
	get_similar_incidents/handler.py enriches this with title/status/resolution_notes via Ticket
	Management's TicketReadRepository.get_similarity_summaries.
	"""

	similar_ticket_id: UUID
	similarity_score: float
	rank: int
