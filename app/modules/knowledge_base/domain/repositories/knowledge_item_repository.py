from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem


class KnowledgeItemRepository(ABC):
	@abstractmethod
	async def add(self, item: KnowledgeItem) -> None:
		raise NotImplementedError

	@abstractmethod
	async def get_by_source(self, source_id: UUID) -> KnowledgeItem | None:
		raise NotImplementedError
