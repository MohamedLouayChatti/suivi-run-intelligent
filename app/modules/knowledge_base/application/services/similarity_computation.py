from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.modules.knowledge_base.application.interfaces.similarity_search_port import SimilaritySearchPort
from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.services.similarity_ranking import (
	ALGORITHM_VERSION,
	MAX_RESULTS,
	MIN_SIMILARITY_THRESHOLD,
	rank_candidates,
)


class SimilarityComputation:
	"""The single definition of how a stored vector becomes its ticket's result rows: the two
	searches, the ranking policy applied to what they return, and the traceability stamped on what
	survives.

	Every path that writes the graph goes through here -- a new ticket's own generation, the
	one-hop neighbour refresh that follows it, and the full rebuild. That is the point of it being
	a collaborator rather than a step written out in each of them: three copies of this sequence
	would not fail if they drifted apart, they would produce a graph whose edges mean subtly
	different things depending on which pass happened to write them, which is not detectable after
	the fact.

	Embeds nothing, deliberately. It works from a KnowledgeItem whose vector already exists, which
	is what lets the refresh and the rebuild recompute results without a model call, and why
	`embedding_model_version` is read off the item rather than off an embedding provider this has
	no reason to know about: the vector being ranked is the one that model produced.
	"""

	def __init__(self, search_port: SimilaritySearchPort) -> None:
		self.search_port = search_port

	async def results_for(self, item: KnowledgeItem, generated_at: datetime) -> list[SimilarityResult]:
		semantic = await self.search_port.find_nearest(
			item.embedding, application=item.application,
			exclude_ticket_id=item.source_id, limit=MAX_RESULTS,
		)
		referenced = await self.search_port.find_referenced(
			item.embedding, item.identifiers,
			application=item.application, exclude_ticket_id=item.source_id,
		)
		ranked = rank_candidates(
			semantic=semantic, referenced=referenced,
			min_similarity_score=MIN_SIMILARITY_THRESHOLD, max_results=MAX_RESULTS,
		)
		return [
			SimilarityResult.create(
				id=uuid4(), source_ticket_id=item.source_id, similar_ticket_id=candidate.ticket_id,
				similarity_score=candidate.similarity_score, rank=candidate.rank,
				generated_at=generated_at, embedding_model_version=item.embedding_model_version,
				algorithm_version=ALGORITHM_VERSION,
			)
			for candidate in ranked
		]
