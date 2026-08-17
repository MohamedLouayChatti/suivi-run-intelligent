from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BackfillKnowledgeItemsCommand:
	"""Embed every ticket that does not have a knowledge item yet.

	`generated_at` is when this pass runs, not when the tickets were created: it stamps when each
	vector was produced, which is the fact a model change needs to reason about. Passed in rather
	than read from the clock inside the handler so one pass stamps one timestamp throughout.

	`batch_size` trades restart cost against round trips. Embeddings within a batch are lost if the
	pass dies mid-batch, so it is also the granularity at which a long run is resumable.
	"""

	generated_at: datetime
	batch_size: int = 25
