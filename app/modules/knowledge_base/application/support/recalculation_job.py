from __future__ import annotations

from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.workers.jobs import WeeklySchedule

# How the recalculation identifies itself to the scheduling infrastructure, and the only name under
# which it is ever registered, rescheduled or logged. Stable by contract: it is the handle the
# configuration update reaches for at runtime, so renaming it would leave the previously registered
# job orphaned and the new schedule pointing at nothing.
SIMILARITY_RECALCULATION_JOB_NAME = "similarity_graph_full_recalculation"


def to_weekly_schedule(schedule: SimilarityRecalculationSchedule) -> WeeklySchedule:
	"""Translate the configured schedule into the scheduler's own vocabulary.

	The two shapes are close enough to look redundant, and are kept apart on purpose: one is this
	module's configuration, with the invariants and the defaults that belong to it, and the other
	is what any recurring job in this codebase needs. Collapsing them would put a knowledge-base
	concept in app/workers/, which is the one thing that package is built not to contain.

	`enabled` is not translated because it is not part of the trigger -- it is passed alongside it,
	since a disabled schedule still has times, it simply does not fire at them.
	"""
	return WeeklySchedule(
		days_of_week=tuple(day.value for day in schedule.days_in_week_order()),
		hour=schedule.hour,
		minute=schedule.minute,
		timezone=schedule.timezone,
	)
