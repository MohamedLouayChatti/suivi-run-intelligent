from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.modules.knowledge_base.domain.repositories.similarity_recalculation_schedule_repository import (
	SimilarityRecalculationScheduleRepository,
)
from app.modules.knowledge_base.domain.repositories.similarity_result_repository import SimilarityResultRepository


class UnitOfWork(ABC):
	"""The transactional half of this module: the similarity graph and the schedule that rebuilds it.

	Knowledge items are deliberately absent. They live in a vector store that shares no transaction
	with Postgres, so exposing them here would promise a commit/rollback that could not cover them
	-- and the handlers that write both need to be written knowing the item write is already
	durable by the time the graph write is attempted. KnowledgeItemRepository is injected alongside
	this instead, the same way SimilaritySearchPort always has been.

	The two repositories here never appear in one transaction: the graph is written by the passes
	that derive it, the schedule only by an administrator changing it. They share this unit of work
	because they share a database, which is the only thing a unit of work is about.
	"""

	similarity_results: SimilarityResultRepository
	recalculation_schedule: SimilarityRecalculationScheduleRepository

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
