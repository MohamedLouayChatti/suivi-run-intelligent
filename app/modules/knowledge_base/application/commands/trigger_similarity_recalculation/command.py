from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TriggerSimilarityRecalculationCommand:
	"""Ask for a full similarity graph recalculation to start now.

	Carries nothing but its actor, because there is nothing to configure about a run: the pass is
	the same one the schedule fires, with the same scope and the same retrieval policy. Anything
	that made a manual run *different* from a scheduled one would produce a graph whose edges
	depend on how they were requested.
	"""

	actor_id: UUID
