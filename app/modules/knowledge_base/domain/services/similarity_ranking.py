from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

# Retrieval policy. MIN_SIMILARITY_THRESHOLD stays a placeholder until an embedding model is
# chosen: cosine scores are not comparable across models (on the historical corpus, 0.6 keeps a
# mean of 6.6 results out of 7 for qwen3-embedding but only 2.9 for embeddinggemma, and leaves
# embeddinggemma returning nothing at all on 17 of 50 queries). The evaluation notebook
# calibrates a threshold per model and the winner's value is what belongs here.
MIN_SIMILARITY_THRESHOLD = 0.6
MAX_RESULTS = 7
ALGORITHM_VERSION = "v2"


@dataclass(frozen=True)
class ScoredCandidate:
	"""A candidate and its cosine similarity, before any policy is applied."""

	ticket_id: UUID
	similarity_score: float


@dataclass(frozen=True)
class RankedCandidate:
	"""A candidate that survived the retrieval policy, with its final 1-based rank."""

	ticket_id: UUID
	similarity_score: float
	rank: int
	matched_reference: bool


def rank_candidates(
	*,
	semantic: Iterable[ScoredCandidate],
	referenced: Iterable[ScoredCandidate] = (),
	min_similarity_score: float = MIN_SIMILARITY_THRESHOLD,
	max_results: int = MAX_RESULTS,
) -> list[RankedCandidate]:
	"""The single definition of how retrieved candidates become final results.

	Lives in the domain, with no dependency on pgvector, SQLAlchemy or the embedding provider, so
	the evaluation notebook can apply the exact same policy to numpy-computed candidates instead
	of reimplementing it. If this function changes, production and the evaluation move together.

	`referenced` are candidates matched on a reference identifier (an incident, commande or
	prestation the query explicitly cites). They are guaranteed a slot: they skip the score
	threshold and are placed ahead of purely semantic matches, because a ticket the query
	literally names is related whatever the cosine says. On the historical corpus this is what
	recovers follow-ups like "Au sujet du ticket INC001010976766", whose target every candidate
	model ranks beyond position 100.

	`semantic` must already arrive best-first, which is what the vector search's ORDER BY
	guarantees. With no reference matches -- the common case -- the output is exactly the
	previous behaviour: threshold, then cap at max_results.
	"""
	ranked: list[RankedCandidate] = []
	seen: set[UUID] = set()

	for candidate in sorted(referenced, key=lambda c: c.similarity_score, reverse=True):
		if candidate.ticket_id in seen:
			continue
		seen.add(candidate.ticket_id)
		ranked.append(
			RankedCandidate(
				ticket_id=candidate.ticket_id, similarity_score=candidate.similarity_score,
				rank=len(ranked) + 1, matched_reference=True,
			)
		)
		if len(ranked) == max_results:
			return ranked

	for candidate in semantic:
		if candidate.ticket_id in seen or candidate.similarity_score < min_similarity_score:
			continue
		seen.add(candidate.ticket_id)
		ranked.append(
			RankedCandidate(
				ticket_id=candidate.ticket_id, similarity_score=candidate.similarity_score,
				rank=len(ranked) + 1, matched_reference=False,
			)
		)
		if len(ranked) == max_results:
			break

	return ranked
