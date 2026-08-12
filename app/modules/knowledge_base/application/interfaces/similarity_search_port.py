from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class SimilarityCandidate:
	ticket_id: UUID
	similarity_score: float


class SimilaritySearchPort(ABC):
	"""Nearest-neighbor vector search. Deliberately NOT part of the UnitOfWork -- it's a read,
	and every read-repository in this codebase stays structurally decoupled from any UoW, kept
	exception-free even though this particular read happens mid-write.

	Candidate search is restricted to `application` at the query level, not post-filtered.
	"""

	@abstractmethod
	async def find_nearest(
		self, embedding: list[float], *, application: Application, exclude_ticket_id: UUID, limit: int,
	) -> list[SimilarityCandidate]:
		raise NotImplementedError
