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
	async def similar_ticket_ids_for_source(self, source_ticket_id: UUID) -> list[UUID]:
		"""The tickets one source currently links to, best-ranked first -- its edges in the graph,
		without the scores or the traceability that come with a full result row.

		This is what "one hop" means concretely. Reading it back from the graph rather than taking
		it from whoever computed it is what keeps the neighbour refresh runnable against any ticket
		id, instead of only in the few lines after a generation happened to hold the same list in
		memory.
		"""
		raise NotImplementedError

	@abstractmethod
	async def delete_all(self) -> None:
		"""Drop the whole graph. Distinct from replace_for_source not in mechanism but in scope:
		this is the model-change path, where every edge in the graph is invalid at once rather than
		one source's edges being superseded."""
		raise NotImplementedError
