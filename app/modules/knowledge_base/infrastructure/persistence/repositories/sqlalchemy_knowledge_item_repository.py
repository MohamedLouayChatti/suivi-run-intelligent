from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectin_polymorphic

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.knowledge_base.infrastructure.persistence import mapper
from app.modules.knowledge_base.infrastructure.persistence.models.knowledge_item_model import (
	KnowledgeItemModel,
	TicketKnowledgeItemModel,
)


class SqlAlchemyKnowledgeItemRepository(KnowledgeItemRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, item: KnowledgeItem) -> None:
		self.session.add(mapper.knowledge_item_to_model(item))

	async def exists(self, source_id: UUID) -> bool:
		stmt = select(exists().where(KnowledgeItemModel.source_id == source_id))
		return bool(await self.session.scalar(stmt))

	async def existing_source_ids(self, source_ids: Sequence[UUID]) -> set[UUID]:
		if not source_ids:
			return set()
		stmt = select(KnowledgeItemModel.source_id).where(KnowledgeItemModel.source_id.in_(source_ids))
		return set(await self.session.scalars(stmt))

	async def list_page(self, *, after_id: UUID | None, limit: int) -> list[KnowledgeItem]:
		stmt = (
			select(KnowledgeItemModel)
			# Subtype columns are not loaded by a base-table query, and reaching for one afterwards
			# would be a lazy load -- which is not merely slow on an async session, it raises. The
			# mapper reads genergy_id off every row, so they have to come eagerly. (`identifiers`
			# needs no option here: that relationship already declares lazy="selectin".)
			.options(selectin_polymorphic(KnowledgeItemModel, [TicketKnowledgeItemModel]))
			.order_by(KnowledgeItemModel.id)
			.limit(limit)
		)
		if after_id is not None:
			stmt = stmt.where(KnowledgeItemModel.id > after_id)
		models = (await self.session.scalars(stmt)).all()
		return [mapper.model_to_knowledge_item(model) for model in models]

	async def distinct_model_versions(self) -> list[tuple[str, str]]:
		stmt = select(KnowledgeItemModel.embedding_model, KnowledgeItemModel.embedding_model_version).distinct()
		return [(model, version) for model, version in (await self.session.execute(stmt)).all()]

	async def delete_all(self) -> None:
		# Against the base table directly rather than the mapped class: this is a joined-table
		# hierarchy, and the subtype and identifier rows are removed by the schema's own
		# ON DELETE CASCADE, so one statement is both sufficient and correct.
		await self.session.execute(delete(KnowledgeItemModel.__table__))
