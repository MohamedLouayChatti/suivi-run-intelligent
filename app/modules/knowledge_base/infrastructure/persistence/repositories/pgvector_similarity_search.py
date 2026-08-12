from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.application.interfaces.similarity_search_port import (
	SimilarityCandidate,
	SimilaritySearchPort,
)
from app.modules.knowledge_base.infrastructure.persistence.models.knowledge_item_model import KnowledgeItemModel
from app.modules.ticket_management.domain.enums.application import Application


class PgvectorSimilaritySearch(SimilaritySearchPort):
	"""Nearest-neighbor search via pgvector's cosine distance operator (`<=>`), converted to a
	similarity score as `1 - distance`. Distance metric and index type (HNSW vs IVFFlat) are
	unconfirmed placeholders. Candidate search is restricted
	to `application` at the query level, never post-filtered.
	"""

	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def find_nearest(
		self, embedding: list[float], *, application: Application, exclude_ticket_id: UUID, limit: int,
	) -> list[SimilarityCandidate]:
		distance = KnowledgeItemModel.embedding.cosine_distance(embedding)
		stmt = (
			select(KnowledgeItemModel.source_id, distance.label("distance"))
			.where(KnowledgeItemModel.application == application)
			.where(KnowledgeItemModel.source_id != exclude_ticket_id)
			.order_by(distance)
			.limit(limit)
		)
		rows = (await self.session.execute(stmt)).all()
		return [
			SimilarityCandidate(ticket_id=source_id, similarity_score=1 - distance_value)
			for source_id, distance_value in rows
		]
