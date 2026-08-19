from __future__ import annotations

from app.shared.exceptions.domain_exceptions import DomainError


class KnowledgeBaseDomainError(DomainError):
	"""Base exception for knowledge base domain errors."""


class InvalidRecalculationSchedule(KnowledgeBaseDomainError):
	"""Base for the ways a recalculation schedule can fail to describe a real recurring moment.

	These are enforced in the domain rather than left to the scheduler because a schedule is
	persisted before it is ever applied: an invalid one that only failed at trigger-construction
	time would already be in the database, and would be re-read and fail again at every startup.
	"""


class EmptyRecalculationSchedule(InvalidRecalculationSchedule):
	"""No weekday was selected.

	Rejected even when the schedule is disabled. "Disabled" already means "does not run", so an
	empty day set adds nothing except an unanswerable question at the moment it is re-enabled.
	"""

	def __init__(self) -> None:
		super().__init__("A recalculation schedule must select at least one weekday.")


class InvalidRecalculationTime(InvalidRecalculationSchedule):
	"""The time of day is not a real one."""

	def __init__(self, hour: int, minute: int) -> None:
		super().__init__(
			f"{hour:02d}:{minute:02d} is not a valid time of day: hour must be 0-23 and minute 0-59."
		)
		self.hour = hour
		self.minute = minute


class UnknownRecalculationTimezone(InvalidRecalculationSchedule):
	"""The timezone is not one this machine can resolve.

	Named IANA zones rather than fixed offsets, so that a schedule set for 20:00 local time stays
	at 20:00 local time across a daylight-saving change instead of drifting by an hour.
	"""

	def __init__(self, timezone: str) -> None:
		super().__init__(f"{timezone!r} is not a known IANA timezone name.")
		self.timezone = timezone
