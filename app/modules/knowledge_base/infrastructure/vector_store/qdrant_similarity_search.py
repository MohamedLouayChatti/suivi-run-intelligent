from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models

from app.modules.knowledge_base.application.interfaces.similarity_search_port import (
	SimilarityCandidate,
	SimilaritySearchPort,
)
from app.modules.knowledge_base.domain.services.description_preprocessor import ExtractedIdentifier
from app.modules.knowledge_base.infrastructure.vector_store import collection, payload
from app.modules.ticket_management.domain.enums.application import Application

# How many reference matches a single query may pull back. The relational query this replaced was
# unbounded, which a vector store has no equivalent of -- every search takes a limit. The number is
# far above what the corpus produces in practice (a description cites a handful of tickets, not
# dozens) and well above MAX_RESULTS, so the ranking policy, not this cap, is what decides which
# matches survive. It exists to stop a pathological description from dragging the whole application
# partition back over the network.
REFERENCE_MATCH_LIMIT = 64


class QdrantSimilaritySearch(SimilaritySearchPort):
	"""Candidate retrieval against the Qdrant collection.

	Both searches restrict to one Application inside the query itself. In this store that is not
	merely a correctness requirement but the cheap path: `application` is indexed as the tenant key,
	so a filtered search walks only that application's own points rather than filtering a global
	result set down afterwards.

	Scores are used as returned. A collection configured for cosine distance scores points by
	cosine similarity directly -- higher is better, already on the scale MIN_SIMILARITY_THRESHOLD
	was calibrated against -- so unlike the distance operator this replaced, nothing here converts
	between the two.
	"""

	def __init__(self, client: AsyncQdrantClient) -> None:
		self.client = client

	async def find_nearest(
		self, embedding: list[float], *, application: Application, exclude_ticket_id: UUID, limit: int,
	) -> list[SimilarityCandidate]:
		response = await self.client.query_points(
			collection_name=collection.COLLECTION_NAME,
			query=embedding,
			query_filter=models.Filter(
				must=[self._in_application(application)],
				must_not=[self._is_source(exclude_ticket_id)],
			),
			limit=limit,
			with_payload=[collection.SOURCE_ID],
			with_vectors=False,
		)
		return self._to_candidates(response.points)

	async def find_referenced(
		self,
		embedding: list[float],
		identifiers: Sequence[ExtractedIdentifier],
		*,
		application: Application,
		exclude_ticket_id: UUID,
	) -> list[SimilarityCandidate]:
		references = [identifier for identifier in identifiers if identifier.type.is_reference]
		if not references:
			return []

		response = await self.client.query_points(
			collection_name=collection.COLLECTION_NAME,
			query=embedding,
			query_filter=models.Filter(
				must=[
					self._in_application(application),
					# Nested `should`: a candidate qualifies if the cited value is either its own
					# ticket's identifier, or one of the identifiers extracted from its description.
					# The first is the case that matters -- a ticket referenced as "suite ticket
					# INC001010948992" does not repeat that string, it *is* the ticket carrying it.
					models.Filter(
						should=[
							models.FieldCondition(
								key=collection.GENERGY_ID,
								match=models.MatchAny(any=[reference.value for reference in references]),
							),
							models.FieldCondition(
								key=collection.REFERENCE_KEYS,
								match=models.MatchAny(
									any=[payload.reference_key(reference) for reference in references]
								),
							),
						]
					),
				],
				must_not=[self._is_source(exclude_ticket_id)],
			),
			limit=REFERENCE_MATCH_LIMIT,
			with_payload=[collection.SOURCE_ID],
			with_vectors=False,
		)
		return self._to_candidates(response.points)

	@staticmethod
	def _in_application(application: Application) -> models.FieldCondition:
		return models.FieldCondition(
			key=collection.APPLICATION, match=models.MatchValue(value=application.value)
		)

	@staticmethod
	def _is_source(ticket_id: UUID) -> models.FieldCondition:
		"""Matched on the payload rather than the point id: the exclusion is "not the ticket being
		queried for", and a ticket's id is not its knowledge item's id."""
		return models.FieldCondition(
			key=collection.SOURCE_ID, match=models.MatchValue(value=str(ticket_id))
		)

	@staticmethod
	def _to_candidates(points: list[models.ScoredPoint]) -> list[SimilarityCandidate]:
		return [
			SimilarityCandidate(
				ticket_id=UUID(point.payload[collection.SOURCE_ID]), similarity_score=point.score
			)
			for point in points
			if point.payload
		]
