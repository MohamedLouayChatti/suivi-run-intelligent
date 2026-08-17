from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult


class SimilarityResultRepository(ABC):
	@abstractmethod
	async def replace_for_source(self, source_ticket_id: UUID, results: list[SimilarityResult]) -> None:
		"""Atomically replace the full result set for one source ticket -- results are always
		regenerated wholesale (generation, incremental refresh, or rebuild), never appended to,
		since a stale row for that source is never valid once new results exist."""
		raise NotImplementedError

	@abstractmethod
	async def delete_all(self) -> None:
		"""Drop the whole graph. Distinct from replace_for_source not in mechanism but in scope:
		this is the model-change path, where every edge in the graph is invalid at once rather than
		one source's edges being superseded."""
		raise NotImplementedError
