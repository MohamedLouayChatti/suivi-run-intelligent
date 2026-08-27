from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime

from app.modules.ticket_management.domain.enums.application import Application

# Below this many days of reconstructed daily-active-count history, or this many resolved
# tickets, a baseline's mean/stddev are too thin to trust as a threshold -- tiering falls back
# to the fixed constants in domain/services/health_tiering.py instead. A read-only check against
# the live database found every one of today's four applications comfortably past both (227-542
# sample days, 54-285 resolved tickets), so this is a safety net for a brand-new application
# rather than something today's data will ever hit.
MIN_ACTIVE_COUNT_SAMPLE_DAYS = 30
MIN_RESOLUTION_SAMPLE_COUNT = 10


@dataclass(frozen=True)
class ApplicationHealthBaseline:
	"""An application's own historical normal for two signals -- daily active-ticket count and
	resolution time -- computed over all available history rather than a fixed window, so a
	slow-moving application's baseline reflects how it actually runs rather than a threshold
	invented for it.

	Thresholds are mean + 1 stddev (warning) / mean + 2 stddev (critical): an application is
	"critical" when a signal is running meaningfully worse than its own history, not against an
	arbitrary number every application was measured against before this.
	"""

	application: Application
	active_count_mean: float
	active_count_median: float
	active_count_max: float
	active_count_stddev: float
	active_count_sample_days: int
	resolution_hours_mean: float
	resolution_hours_median: float
	resolution_hours_max: float
	resolution_hours_stddev: float
	resolution_hours_sample_count: int
	computed_at: datetime

	@property
	def active_count_warning_threshold(self) -> float:
		return self.active_count_mean + self.active_count_stddev

	@property
	def active_count_critical_threshold(self) -> float:
		return self.active_count_mean + 2 * self.active_count_stddev

	@property
	def resolution_hours_warning_threshold(self) -> float:
		return self.resolution_hours_mean + self.resolution_hours_stddev

	@property
	def resolution_hours_critical_threshold(self) -> float:
		return self.resolution_hours_mean + 2 * self.resolution_hours_stddev

	@property
	def active_count_meets_minimum_sample(self) -> bool:
		return self.active_count_sample_days >= MIN_ACTIVE_COUNT_SAMPLE_DAYS

	@property
	def resolution_hours_meets_minimum_sample(self) -> bool:
		return self.resolution_hours_sample_count >= MIN_RESOLUTION_SAMPLE_COUNT

	@classmethod
	def compute(
		cls, *, application: Application, daily_active_counts: list[int],
		resolution_hours: list[float], computed_at: datetime,
	) -> ApplicationHealthBaseline:
		return cls(
			application=application,
			active_count_mean=_mean(daily_active_counts),
			active_count_median=_median(daily_active_counts),
			active_count_max=float(max(daily_active_counts)) if daily_active_counts else 0.0,
			active_count_stddev=_stdev(daily_active_counts),
			active_count_sample_days=len(daily_active_counts),
			resolution_hours_mean=_mean(resolution_hours),
			resolution_hours_median=_median(resolution_hours),
			resolution_hours_max=float(max(resolution_hours)) if resolution_hours else 0.0,
			resolution_hours_stddev=_stdev(resolution_hours),
			resolution_hours_sample_count=len(resolution_hours),
			computed_at=computed_at,
		)


def _mean(values: list[int] | list[float]) -> float:
	return float(statistics.mean(values)) if values else 0.0


def _median(values: list[int] | list[float]) -> float:
	return float(statistics.median(values)) if values else 0.0


def _stdev(values: list[int] | list[float]) -> float:
	# A single sample has no spread to measure -- statistics.stdev itself refuses it with
	# StatisticsError, and 0.0 is the honest answer rather than a workaround for one.
	return float(statistics.stdev(values)) if len(values) >= 2 else 0.0
