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
