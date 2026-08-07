from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KpiTotalsDTO:
	"""Raw numbers for a single window -- the repository computes this once per window;
	the handler calls it twice (current + previous) and derives KpiTrendsDTO."""

	total_tickets: int
	open_tickets: int
	resolved_tickets: int
	avg_resolution_hours: float
	urgent_tickets: int


@dataclass(frozen=True)
class KpiTrendsDTO:
	"""Percentage change of each KPI vs the immediately preceding period of equal length."""

	total_tickets: float
	open_tickets: float
	resolved_tickets: float
	avg_resolution_hours: float
	urgent_tickets: float


@dataclass(frozen=True)
class KpiSnapshotDTO:
	total_tickets: int
	open_tickets: int
	resolved_tickets: int
	avg_resolution_hours: float
	urgent_tickets: int
	trends: KpiTrendsDTO
