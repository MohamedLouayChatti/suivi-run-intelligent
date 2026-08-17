from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RebuildSimilarityGraphCommand:
	"""Recompute every source ticket's similar-incident results from the vectors already stored.

	Embeds nothing. That is the whole point of the split: a threshold or ranking change invalidates
	the graph but not the vectors, and re-deriving the graph is a pure database operation, orders of
	magnitude cheaper than re-embedding the corpus.

	`batch_size` is larger than the backfill's by default because a batch here costs a few indexed
	queries per item rather than a model call per item.
	"""

	generated_at: datetime
	batch_size: int = 100
