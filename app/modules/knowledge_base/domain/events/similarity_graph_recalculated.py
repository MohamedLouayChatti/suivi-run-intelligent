from __future__ import annotations

from dataclasses import dataclass

from app.modules.knowledge_base.domain.enums.recalculation_trigger import RecalculationTrigger
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class SimilarityGraphRecalculated(DomainEvent):
	"""Every source ticket's similar-incident results were recomputed from the stored corpus.

	The largest single change this system makes to itself: one pass rewrites the whole graph that
	every engineer's similar-incident card reads from. Until now its only trace was a log line,
	which is a poor home for the fact an administrator keeps asking for -- when this last actually
	ran, and whether it found anything.

	Recording it is what lets a run history exist without a run-history table: an audit log
	filtered by this event type answers "when did the last pass run" from rows that are written
	anyway. That is a deliberate revision of the earlier decision to leave last_run_at out of the
	API for want of somewhere to keep it.

	Distinct from SimilarityResultsGenerated, which stays exactly what it was -- one newly created
	ticket now has similar incidents to look at. This one says the derived data was re-derived, and
	it is emitted once per pass rather than once per source, for the same reason the pass itself
	stays silent per row.

	actor_id is always None. Two of the three triggers have no actor at all, and attributing a
	scheduled pass to whoever last touched the schedule would be a guess dressed as a record;
	SimilarityRecalculationRequested is where the manual trigger's actor lives.
	"""

	trigger: RecalculationTrigger
	items_processed: int
	results_written: int
	sources_without_results: int
	duration_seconds: float
