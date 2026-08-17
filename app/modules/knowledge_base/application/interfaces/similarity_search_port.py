from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.modules.knowledge_base.domain.services.description_preprocessor import ExtractedIdentifier
from app.modules.knowledge_base.domain.services.similarity_ranking import ScoredCandidate
from app.modules.ticket_management.domain.enums.application import Application

# Kept as an alias so existing references to SimilarityCandidate keep working; the type itself now
# lives in the domain because the ranking service it feeds is domain logic.
SimilarityCandidate = ScoredCandidate


class SimilaritySearchPort(ABC):
	"""Candidate retrieval -- semantic and exact. Deliberately NOT part of the UnitOfWork: it's a
	read, and every read-repository in this codebase stays structurally decoupled from any UoW,
	kept exception-free even though this particular read happens mid-write.

	Both methods restrict candidates to `application` at the query level, never post-filtered.
	"""

	@abstractmethod
	async def find_nearest(
		self, embedding: list[float], *, application: Application, exclude_ticket_id: UUID, limit: int,
	) -> list[SimilarityCandidate]:
		"""Nearest neighbours by vector distance, best first."""
		raise NotImplementedError

	@abstractmethod
	async def find_referenced(
		self,
		embedding: list[float],
		identifiers: Sequence[ExtractedIdentifier],
		*,
		application: Application,
		exclude_ticket_id: UUID,
	) -> list[SimilarityCandidate]:
		"""Items the query explicitly references, by exact identifier match.

		A candidate matches when a cited reference identifier is either its own ticket's
		genergy_id, or one of the identifiers extracted from its description. The first case is
		the one that matters most: a ticket referenced as "suite ticket INC001010948992" does not
		repeat that string in its description -- it is the ticket whose genergy_id *is* that
		value.

		Takes `embedding` only so the returned candidates carry their real cosine similarity;
		these results bypass the score threshold, they are not scored by it. Effectively unbounded:
		the caller's ranking policy, not this call, decides how many survive. An implementation may
		impose a cap far above what a description can realistically cite, as a guard rather than a
		policy.
		"""
		raise NotImplementedError
