from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.application.interfaces.similarity_search_port import (
	SimilarityCandidate,
	SimilaritySearchPort,
)
from app.modules.knowledge_base.domain.services.description_preprocessor import ExtractedIdentifier
from app.modules.knowledge_base.infrastructure.persistence.models.knowledge_item_model import (
	KnowledgeItemIdentifierModel,
	KnowledgeItemModel,
	TicketKnowledgeItemModel,
)
from app.modules.ticket_management.domain.enums.application import Application


class PgvectorSimilaritySearch(SimilaritySearchPort):
	"""Candidate search via pgvector's cosine distance operator (`<=>`), converted to a
	similarity score as `1 - distance`. Distance metric and index type (HNSW vs IVFFlat) are
	unconfirmed placeholders. Candidate search is restricted to `application` at the query level,
	never post-filtered.
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

		# Joined against the raw subtype table rather than the mapped subclass: this is a base-table
		# query that merely needs one subtype column, and an explicit outer join keeps it a single
		# statement without pulling the whole polymorphic selectable into it.
		ticket_items = TicketKnowledgeItemModel.__table__

		identifier_match = (
			select(KnowledgeItemIdentifierModel.id)
			.where(KnowledgeItemIdentifierModel.knowledge_item_id == KnowledgeItemModel.id)
			.where(
				tuple_(
					KnowledgeItemIdentifierModel.identifier_type, KnowledgeItemIdentifierModel.value
				).in_([(reference.type, reference.value) for reference in references])
			)
			.exists()
		)

		distance = KnowledgeItemModel.embedding.cosine_distance(embedding)
		stmt = (
			select(KnowledgeItemModel.source_id, distance.label("distance"))
			.outerjoin(ticket_items, ticket_items.c.id == KnowledgeItemModel.id)
			.where(KnowledgeItemModel.application == application)
			.where(KnowledgeItemModel.source_id != exclude_ticket_id)
			.where(
				or_(
					ticket_items.c.genergy_id.in_([reference.value for reference in references]),
					identifier_match,
				)
			)
			.order_by(distance)
		)
		rows = (await self.session.execute(stmt)).all()
		return [
			SimilarityCandidate(ticket_id=source_id, similarity_score=1 - distance_value)
			for source_id, distance_value in rows
		]
