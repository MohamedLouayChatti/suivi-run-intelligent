from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.knowledge_base.application.dto.recalculation_schedule_dto import RecalculationScheduleDTO
from app.modules.knowledge_base.domain.enums.weekday import Weekday


class UpdateRecalculationScheduleRequest(BaseModel):
	"""The whole schedule, not a patch of one -- the fields are meaningless apart from each other.

	The bounds here duplicate the domain's invariants deliberately: this is the adapter's job (a
	malformed request should be a 422 naming the field, not a domain error), and the domain checks
	them again because HTTP is not the only way a schedule can be built.
	"""

	enabled: bool
	days_of_week: set[Weekday] = Field(min_length=1)
	hour: int = Field(ge=0, le=23)
	minute: int = Field(ge=0, le=59)
	# An IANA zone name. Left as a plain string rather than an enumeration: the set of valid zones
	# belongs to the machine's tz database, and the domain rejects anything it cannot resolve.
	timezone: str = "UTC"


class RecalculationScheduleResponse(BaseModel):
	"""The configured schedule, plus what the scheduler currently makes of it."""

	enabled: bool
	days_of_week: list[Weekday]
	hour: int
	minute: int
	timezone: str
	next_run_at: datetime | None
	running: bool
	updated_at: datetime | None
	updated_by: UUID | None

	@classmethod
	def from_dto(cls, schedule: RecalculationScheduleDTO) -> RecalculationScheduleResponse:
		return cls(
			enabled=schedule.enabled,
			days_of_week=list(schedule.days_of_week),
			hour=schedule.hour,
			minute=schedule.minute,
			timezone=schedule.timezone,
			next_run_at=schedule.next_run_at,
			running=schedule.running,
			updated_at=schedule.updated_at,
			updated_by=schedule.updated_by,
		)
