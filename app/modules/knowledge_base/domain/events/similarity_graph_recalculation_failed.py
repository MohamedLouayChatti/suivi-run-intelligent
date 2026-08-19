from __future__ import annotations

from dataclasses import dataclass

from app.modules.knowledge_base.domain.enums.recalculation_trigger import RecalculationTrigger
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class SimilarityGraphRecalculationFailed(DomainEvent):
	"""A full recalculation started and did not finish.

	This is the event that pays for the rest. A failed pass leaves the previous graph as it was --
	stale but coherent -- and says so nowhere: every engineer keeps seeing results computed against
	an older corpus, the schedule keeps its next firing, and the only record is a log line nobody
	reads at 20:00 on a Tuesday. Days of silent staleness is a poor default for the module whose
	whole purpose is surfacing what the organization already knows.

	Publishing it does not change the failure policy it reports on. The pass still raises, the job
	runner still logs it against the job name, there is still no retry, and the schedule is still
	the retry that matters -- this is caught, announced and re-raised, so nothing is swallowed on
	the way past.

	reason is the failure as it presented itself, which for the two that actually happen is the
	useful half: an unreachable vector store reads differently from a mixed-model corpus, and only
	one of them is repaired by waiting for the next run.
	"""

	trigger: RecalculationTrigger
	reason: str
	duration_seconds: float
