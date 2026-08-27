from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from app.modules.analytics.application.commands.recalculate_application_health_baselines.command import (
	RecalculateApplicationHealthBaselinesCommand,
)
from app.modules.analytics.application.interfaces.health_history_read_repository import HealthHistoryReadRepository
from app.modules.analytics.application.interfaces.unit_of_work import UnitOfWork
from app.modules.analytics.domain.services.daily_active_count_reconstruction import reconstruct_daily_active_counts
from app.modules.analytics.domain.value_objects.application_health_baseline import ApplicationHealthBaseline
from app.modules.ticket_management.domain.enums.application import Application

logger = logging.getLogger(__name__)


class RecalculateApplicationHealthBaselinesHandler:
	"""Recomputes every application's baseline from its own all-time history.

	One UnitOfWork per application rather than one for the whole pass, mirroring Knowledge
	Base's per-page commit in its recalculation runner: a failure computing or persisting one
	application's baseline must not lose the other three, since each is an independent
	recomputation with nothing shared between them.
	"""

	def __init__(self, history: HealthHistoryReadRepository, uow_factory: Callable[[], UnitOfWork]) -> None:
		self.history = history
		self.uow_factory = uow_factory

	async def handle(self, command: RecalculateApplicationHealthBaselinesCommand) -> None:
		computed_at = datetime.now(UTC)
		for application in Application:
			events = await self.history.get_ticket_lifecycle_events(application)
			resolution_hours = await self.history.get_resolution_hours_history(application)
			daily_active_counts = reconstruct_daily_active_counts(events, as_of=computed_at.date())
			baseline = ApplicationHealthBaseline.compute(
				application=application, daily_active_counts=daily_active_counts,
				resolution_hours=resolution_hours, computed_at=computed_at,
			)
			async with self.uow_factory() as uow:
				await uow.health_baselines.upsert(baseline)
				await uow.commit()
			logger.info(
				"Application health baseline recalculated for %s: active_count_mean=%.2f (n=%d), "
				"resolution_hours_mean=%.1f (n=%d).",
				application.value, baseline.active_count_mean, baseline.active_count_sample_days,
				baseline.resolution_hours_mean, baseline.resolution_hours_sample_count,
			)
