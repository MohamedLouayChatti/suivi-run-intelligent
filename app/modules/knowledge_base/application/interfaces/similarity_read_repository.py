from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.knowledge_base.application.dto.similarity_result_row_dto import SimilarityResultRowDTO


class SimilarityReadRepository(ABC):
	@abstractmethod
	async def get_for_source(self, source_ticket_id: UUID) -> list[SimilarityResultRowDTO]:
		"""Plain synchronous DB read, ordered by rank -- must never trigger embedding or vector
		search itself."""
		raise NotImplementedError
