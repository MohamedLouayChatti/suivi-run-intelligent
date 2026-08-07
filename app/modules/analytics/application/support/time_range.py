from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class TimeRange(StrEnum):
	LAST_30_DAYS = "30D"
	LAST_3_MONTHS = "3M"
	LAST_6_MONTHS = "6M"
	LAST_YEAR = "1Y"


_RANGE_DAYS: dict[TimeRange, int] = {
	TimeRange.LAST_30_DAYS: 30,
	TimeRange.LAST_3_MONTHS: 90,
	TimeRange.LAST_6_MONTHS: 182,
	TimeRange.LAST_YEAR: 365,
}

# Activity-trend bucketing: how many points to plot and how many days each one spans.
# 30D -> one point per day, 3M -> one per week, 6M/1Y -> one per (roughly) month.
_BUCKET_COUNT: dict[TimeRange, int] = {
	TimeRange.LAST_30_DAYS: 30,
	TimeRange.LAST_3_MONTHS: 13,
	TimeRange.LAST_6_MONTHS: 6,
	TimeRange.LAST_YEAR: 12,
}
_BUCKET_SPAN_DAYS: dict[TimeRange, int] = {
	TimeRange.LAST_30_DAYS: 1,
	TimeRange.LAST_3_MONTHS: 7,
	TimeRange.LAST_6_MONTHS: 30,
	TimeRange.LAST_YEAR: 30,
}


@dataclass(frozen=True, slots=True)
class DateWindow:
	start: datetime
	end: datetime


@dataclass(frozen=True, slots=True)
class ComparisonWindow:
	"""The selected window plus the immediately preceding window of equal length,
	used to compute "vs previous period" trend percentages."""

	current: DateWindow
	previous: DateWindow


def resolve_window(time_range: TimeRange, *, now: datetime | None = None) -> ComparisonWindow:
	end = now or datetime.now(UTC)
	days = _RANGE_DAYS[time_range]
	current_start = end - timedelta(days=days)
	previous_start = current_start - timedelta(days=days)
	return ComparisonWindow(current=DateWindow(current_start, end), previous=DateWindow(previous_start, current_start))


def bucket_scheme(time_range: TimeRange) -> tuple[int, int]:
	"""Returns (bucket_count, bucket_span_days) for the activity-trend chart."""
	return _BUCKET_COUNT[time_range], _BUCKET_SPAN_DAYS[time_range]


def trend_pct(current: float, previous: float) -> float:
	"""Percentage change of `current` vs `previous`. 0 -> 0 stays flat; growth from a
	zero baseline is reported as +100% rather than an undefined/infinite ratio."""
	if previous == 0:
		return 0.0 if current == 0 else 100.0
	return round((current - previous) / previous * 100, 1)
