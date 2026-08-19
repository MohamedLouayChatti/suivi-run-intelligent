from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.knowledge_base.domain.enums.weekday import Weekday, in_week_order
from app.modules.knowledge_base.domain.exceptions import (
	EmptyRecalculationSchedule,
	InvalidRecalculationTime,
	UnknownRecalculationTimezone,
)

# The schedule in force when no administrator has configured one: the expensive full pass twice a
# week, outside working hours. These constants are the default -- there is deliberately no seeded
# row, no migration insert and nothing to run before the application works, so "the default" is
# always this literal rather than a copy of it that drifted.
DEFAULT_DAYS_OF_WEEK: frozenset[Weekday] = frozenset({Weekday.TUESDAY, Weekday.FRIDAY})
DEFAULT_HOUR = 20
DEFAULT_MINUTE = 0
DEFAULT_TIMEZONE = "UTC"
DEFAULT_ENABLED = True


@dataclass(frozen=True)
class SimilarityRecalculationSchedule:
	"""When the full similarity graph recalculation runs, as an administrator configured it.

	A value object, not an aggregate: there is exactly one of these for the installation, it has no
	identity worth referring to, and every change replaces it whole. It carries the invariants that
	make it a real recurring moment -- a non-empty set of days, a real time of day, a resolvable
	timezone -- because it is persisted before it is ever handed to a scheduler, and an invalid one
	would otherwise be discovered only when it was read back at the next startup.

	It describes *when*, never *what*: the pass it schedules is
	RebuildSimilarityGraphCommand, whose semantics (which items are eligible, the similarity
	threshold, the result cap, how results are replaced) belong entirely to that command and are
	unaffected by anything here. That separation is the point -- the schedule is configuration, the
	recalculation is behaviour, and only one of the two is an administrator's to change.

	`updated_at`/`updated_by` are None only for the code default, which by definition nobody has
	saved yet.
	"""

	enabled: bool
	days_of_week: frozenset[Weekday]
	hour: int
	minute: int
	timezone: str
	updated_at: datetime | None = None
	updated_by: UUID | None = None

	@classmethod
	def create(
		cls, *, enabled: bool, days_of_week: frozenset[Weekday], hour: int, minute: int,
		timezone: str, updated_at: datetime | None = None, updated_by: UUID | None = None,
	) -> SimilarityRecalculationSchedule:
		if not days_of_week:
			raise EmptyRecalculationSchedule()
		if not (0 <= hour <= 23 and 0 <= minute <= 59):
			raise InvalidRecalculationTime(hour, minute)
		cls._assert_known_timezone(timezone)
		return cls(
			enabled=enabled, days_of_week=days_of_week, hour=hour, minute=minute,
			timezone=timezone, updated_at=updated_at, updated_by=updated_by,
		)

	@classmethod
	def default(cls) -> SimilarityRecalculationSchedule:
		"""The schedule in force until someone changes it."""
		return cls(
			enabled=DEFAULT_ENABLED, days_of_week=DEFAULT_DAYS_OF_WEEK, hour=DEFAULT_HOUR,
			minute=DEFAULT_MINUTE, timezone=DEFAULT_TIMEZONE,
		)

	def days_in_week_order(self) -> tuple[Weekday, ...]:
		"""The configured days, Monday first -- the stable order every caller shows them in."""
		return in_week_order(self.days_of_week)

	@staticmethod
	def _assert_known_timezone(timezone: str) -> None:
		try:
			ZoneInfo(timezone)
		except (ZoneInfoNotFoundError, ValueError) as exc:
			raise UnknownRecalculationTimezone(timezone) from exc
