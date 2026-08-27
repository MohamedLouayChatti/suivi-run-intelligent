from __future__ import annotations

from app.modules.analytics.domain.enums.health_level import HealthLevel
from app.modules.analytics.domain.value_objects.application_health_baseline import ApplicationHealthBaseline

# Fallback tiering, used only when a baseline is missing or below its minimum sample -- a safety
# net for an application with no history yet, not a value tuned against real usage, since every
# one of today's four applications will always have a real baseline instead. The resolution pair
# is what this module used unconditionally before baselines existed. The active-count pair is new
# and was sized against the rough magnitude already observed across applications (daily active
# counts: means 0.3-2.3, maxes 3-10, stddevs 0.6-2.1) rather than calibrated the way the real
# baseline is.
RESOLUTION_GOOD_MAX_HOURS_FALLBACK = 12.0
RESOLUTION_WARNING_MAX_HOURS_FALLBACK = 24.0
ACTIVE_COUNT_GOOD_MAX_FALLBACK = 3
ACTIVE_COUNT_WARNING_MAX_FALLBACK = 6

_HEALTH_RANK = {HealthLevel.GOOD: 0, HealthLevel.WARNING: 1, HealthLevel.CRITICAL: 2}


def worse(a: HealthLevel, b: HealthLevel) -> HealthLevel:
	return a if _HEALTH_RANK[a] >= _HEALTH_RANK[b] else b


def active_count_tier(active_tickets: int, baseline: ApplicationHealthBaseline | None) -> HealthLevel:
	if baseline is None or not baseline.active_count_meets_minimum_sample:
		if active_tickets <= ACTIVE_COUNT_GOOD_MAX_FALLBACK:
			return HealthLevel.GOOD
		if active_tickets <= ACTIVE_COUNT_WARNING_MAX_FALLBACK:
			return HealthLevel.WARNING
		return HealthLevel.CRITICAL
	if active_tickets <= baseline.active_count_warning_threshold:
		return HealthLevel.GOOD
	if active_tickets <= baseline.active_count_critical_threshold:
		return HealthLevel.WARNING
	return HealthLevel.CRITICAL


def resolution_tier(avg_resolution_hours: float, baseline: ApplicationHealthBaseline | None) -> HealthLevel:
	if baseline is None or not baseline.resolution_hours_meets_minimum_sample:
		if avg_resolution_hours <= RESOLUTION_GOOD_MAX_HOURS_FALLBACK:
			return HealthLevel.GOOD
		if avg_resolution_hours <= RESOLUTION_WARNING_MAX_HOURS_FALLBACK:
			return HealthLevel.WARNING
		return HealthLevel.CRITICAL
	if avg_resolution_hours <= baseline.resolution_hours_warning_threshold:
		return HealthLevel.GOOD
	if avg_resolution_hours <= baseline.resolution_hours_critical_threshold:
		return HealthLevel.WARNING
	return HealthLevel.CRITICAL


def combined_tier(
	active_tickets: int, avg_resolution_hours: float, baseline: ApplicationHealthBaseline | None,
) -> HealthLevel:
	"""Whichever signal is worse wins: an application is only "good" if both are good."""
	return worse(resolution_tier(avg_resolution_hours, baseline), active_count_tier(active_tickets, baseline))
