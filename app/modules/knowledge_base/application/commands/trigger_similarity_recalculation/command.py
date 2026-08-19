from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class TriggerSimilarityRecalculationCommand:
	"""Ask for a full similarity graph recalculation to start now.

	Carries nothing but its actor and the moment they asked, because there is nothing to configure
	about a run: the pass is the same one the schedule fires, with the same scope and the same
	retrieval policy. Anything that made a manual run *different* from a scheduled one would
	produce a graph whose edges depend on how they were requested.

	`requested_at` is the request's own clock reading, supplied by the route like every other
	timestamp in this codebase rather than read inside the handler. It stamps the event this
	publishes, which is deliberately the moment the administrator asked -- not the moment the pass
	eventually starts, which is the runner's to record and may be minutes later.
	"""

	actor_id: UUID
	requested_at: datetime
