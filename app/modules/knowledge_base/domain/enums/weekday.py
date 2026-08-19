from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum


class Weekday(StrEnum):
	"""A day of the week, valued as the three-letter code cron vocabulary uses.

	The values are chosen to be what a cron trigger already accepts, so a configured schedule
	reaches the scheduler without a translation table in between. That is the only concession this
	enum makes to how the schedule is executed -- nothing else in the module depends on the value
	being anything in particular.
	"""

	MONDAY = "mon"
	TUESDAY = "tue"
	WEDNESDAY = "wed"
	THURSDAY = "thu"
	FRIDAY = "fri"
	SATURDAY = "sat"
	SUNDAY = "sun"


# Declaration order is week order, and iterating the enum preserves it. Named separately because a
# configured set of days is a frozenset -- unordered by nature -- and every place one is shown or
# handed on wants the same stable order rather than whatever the set happens to iterate in.
ORDERED_WEEKDAYS: tuple[Weekday, ...] = tuple(Weekday)


def in_week_order(days: Iterable[Weekday]) -> tuple[Weekday, ...]:
	"""The given days, Monday first, each at most once."""
	selected = set(days)
	return tuple(day for day in ORDERED_WEEKDAYS if day in selected)
