from __future__ import annotations

from uuid import UUID

from sqlalchemy import exists, select
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

	async def exists(self, source_id: UUID) -> bool:
		stmt = select(exists().where(KnowledgeItemModel.source_id == source_id))
		return bool(await self.session.scalar(stmt))
