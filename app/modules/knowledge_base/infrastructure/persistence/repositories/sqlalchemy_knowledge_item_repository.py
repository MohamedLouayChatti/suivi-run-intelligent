from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.knowledge_base.infrastructure.persistence import mapper
from app.modules.knowledge_base.infrastructure.persistence.models.knowledge_item_model import KnowledgeItemModel


class SqlAlchemyKnowledgeItemRepository(KnowledgeItemRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, item: KnowledgeItem) -> None:
		self.session.add(mapper.knowledge_item_to_model(item))

	async def get_by_source(self, source_id: UUID) -> KnowledgeItem | None:
		model = await self.session.scalar(select(KnowledgeItemModel).where(KnowledgeItemModel.source_id == source_id))
		if model is None:
			return None
		return mapper.model_to_knowledge_item(model)
