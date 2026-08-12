from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.knowledge_base.domain.repositories.similarity_result_repository import SimilarityResultRepository


class UnitOfWork(ABC):
	knowledge_items: KnowledgeItemRepository
	similarity_results: SimilarityResultRepository

	@abstractmethod
	async def commit(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def rollback(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def close(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def __aenter__(self) -> Self:
		raise NotImplementedError

	@abstractmethod
	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		raise NotImplementedError
