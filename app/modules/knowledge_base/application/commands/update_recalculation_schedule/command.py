from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.knowledge_base.domain.enums.weekday import Weekday


@dataclass(frozen=True)
class UpdateRecalculationScheduleCommand:
	"""Replace the configured full-recalculation schedule.

	A whole schedule rather than a patch of one: the fields are meaningless apart from each other
	-- days without a time, a time without a timezone -- and validating a partial change would mean
	merging it against the stored row first. There is one of these values, and it is set as a
	whole.

	`actor_id` follows the convention every other mutating command here uses: it is
	`current_user.id`, plumbed from the route, and it is what makes the stored schedule attributable
	to whoever last changed it.
	"""

	enabled: bool
	days_of_week: frozenset[Weekday]
	hour: int
	minute: int
	timezone: str
	updated_at: datetime
	actor_id: UUID
