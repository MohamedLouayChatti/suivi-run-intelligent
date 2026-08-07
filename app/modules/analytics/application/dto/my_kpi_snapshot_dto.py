from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MyKpiSnapshotDTO:
	"""The Dashboard's personal KPI tiles -- scoped to the caller as assignee, over a
	fixed trailing 7-day window (no user-facing time-range selector on that page, unlike
	the Analytics page). No trend comparison, matching KpiCards (no trend row)."""

	resolved_this_week: int
	created_this_week: int
	avg_resolution_hours: float
