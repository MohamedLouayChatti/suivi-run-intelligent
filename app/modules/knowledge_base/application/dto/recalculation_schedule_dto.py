from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.modules.knowledge_base.domain.enums.weekday import Weekday


@dataclass(frozen=True)
class RecalculationScheduleDTO:
	"""The configured schedule plus what the scheduler currently makes of it.

	Three sources in one read, which is the whole reason this is a DTO rather than the entity: the
	persisted configuration, the next firing APScheduler has computed from it, and whether a pass
	is running right now. Only the first is stored -- the other two are derived state read straight
	off the running process, so they cost nothing and can never disagree with reality the way a
	persisted copy of them would.

	`next_run_at` is None whenever the schedule is disabled, which is the same answer as "never
	registered" on purpose: in both cases nothing is going to happen on its own.
	"""

	enabled: bool
	days_of_week: tuple[Weekday, ...]
	hour: int
	minute: int
	timezone: str
	next_run_at: datetime | None
	running: bool
	updated_at: datetime | None
	updated_by: UUID | None

	@classmethod
	def from_schedule(
		cls, schedule: SimilarityRecalculationSchedule, *, next_run_at: datetime | None, running: bool,
	) -> RecalculationScheduleDTO:
		return cls(
			enabled=schedule.enabled,
			days_of_week=schedule.days_in_week_order(),
			hour=schedule.hour,
			minute=schedule.minute,
			timezone=schedule.timezone,
			next_run_at=next_run_at,
			running=running,
			updated_at=schedule.updated_at,
			updated_by=schedule.updated_by,
		)
