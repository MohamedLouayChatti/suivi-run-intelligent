from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RefreshNeighborSimilarityCommand:
	"""Refresh the one-hop neighbourhood of one ticket.

	Carries the source rather than the neighbours. Which tickets that means is read from the graph
	by the handler, so this command is constructible for any ticket id -- not only in the moment
	right after a generation happened to compute the same list in memory -- and the definition of
	"one hop" stays inside the handler that implements it.

	`generated_at` stamps the refreshed rows. It is the triggering event's timestamp rather than a
	clock read mid-handler, so every row one ticket creation produces -- the new ticket's own and
	its neighbours' -- carries the same generation time and the whole hop reads back as one act.
	"""

	source_ticket_id: UUID
	generated_at: datetime
