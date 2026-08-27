from __future__ import annotations

from datetime import UTC, datetime

from app.modules.analytics.application.commands.check_application_health.command import (
	CheckApplicationHealthCommand,
)
from app.modules.analytics.application.interfaces.admin_analytics_read_repository import AdminAnalyticsReadRepository
from app.modules.analytics.application.interfaces.unit_of_work import UnitOfWork
from app.modules.analytics.application.support.time_range import window_for_days
from app.modules.analytics.domain.enums.health_level import HealthLevel
from app.modules.analytics.domain.events.application_health_became_critical import ApplicationHealthBecameCritical
from app.modules.analytics.domain.services import health_tiering
from app.modules.analytics.domain.value_objects.application_health_status import ApplicationHealthStatus
from app.shared.events.event_publisher import EventPublisher

# No user-selected time_range exists in a background job -- fixed to match the dashboard's other
# default-30-day windows, and the same window shape the fixed-constant tiering used before it.
_HEALTH_CHECK_WINDOW_DAYS = 30


class CheckApplicationHealthHandler:
	"""Re-evaluates one application's live signals against its cached baseline, persists the new
	tier, and announces only a transition into CRITICAL -- a re-check that finds an application
	still critical updates the stored status but publishes nothing, since the notification
	already went out once for this incident."""

	def __init__(self, signals: AdminAnalyticsReadRepository, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.signals = signals
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: CheckApplicationHealthCommand) -> None:
		window = window_for_days(_HEALTH_CHECK_WINDOW_DAYS)
		signal = await self.signals.get_health_signal(command.application, window)
		baseline = await self.uow.health_baselines.get(command.application)
		new_tier = health_tiering.combined_tier(signal.active_tickets, signal.avg_resolution_hours, baseline)

		previous_status = await self.uow.health_statuses.get(command.application)
		previous_tier = previous_status.health_level if previous_status is not None else HealthLevel.GOOD

		now = datetime.now(UTC)
		await self.uow.health_statuses.upsert(
			ApplicationHealthStatus(
				application=command.application, health_level=new_tier,
				active_tickets=signal.active_tickets, avg_resolution_hours=signal.avg_resolution_hours,
				updated_at=now,
			)
		)
		await self.uow.commit()

		if new_tier != HealthLevel.CRITICAL or previous_tier == HealthLevel.CRITICAL:
			return

		# Baselines always exist for today's four applications (see the sample-size note in
		# application_health_baseline.py); a missing or thin one falls back to the fixed
		# constant that marks the fallback tiering's own boundary into CRITICAL, since there is
		# no mean/stddev to report a threshold from.
		if baseline is not None and baseline.active_count_meets_minimum_sample:
			active_threshold = baseline.active_count_critical_threshold
		else:
			active_threshold = float(health_tiering.ACTIVE_COUNT_WARNING_MAX_FALLBACK)
		if baseline is not None and baseline.resolution_hours_meets_minimum_sample:
			resolution_threshold = baseline.resolution_hours_critical_threshold
		else:
			resolution_threshold = health_tiering.RESOLUTION_WARNING_MAX_HOURS_FALLBACK

		await self.event_publisher.publish(
			ApplicationHealthBecameCritical(
				application=command.application, previous_health_level=previous_tier,
				active_tickets=signal.active_tickets, avg_resolution_hours=signal.avg_resolution_hours,
				active_count_critical_threshold=active_threshold,
				resolution_hours_critical_threshold=resolution_threshold,
				occurred_at=now,
			)
		)
