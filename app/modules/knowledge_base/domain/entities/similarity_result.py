from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SimilarityResult:
	"""A derived, directed relationship between two tickets -- never part of the Ticket
	aggregate, never assumed reciprocal, always recomputable.
	"""

	id: UUID
	source_ticket_id: UUID
	similar_ticket_id: UUID
	similarity_score: float
	rank: int
	matched_reference: bool
	generated_at: datetime
	embedding_model_version: str
	algorithm_version: str

	@classmethod
	def create(
		cls, *, id: UUID, source_ticket_id: UUID, similar_ticket_id: UUID,
		similarity_score: float, rank: int, matched_reference: bool, generated_at: datetime,
		embedding_model_version: str, algorithm_version: str,
	) -> SimilarityResult:
		return cls(
			id=id, source_ticket_id=source_ticket_id, similar_ticket_id=similar_ticket_id,
			similarity_score=similarity_score, rank=rank, matched_reference=matched_reference,
			generated_at=generated_at, embedding_model_version=embedding_model_version,
			algorithm_version=algorithm_version,
		)
