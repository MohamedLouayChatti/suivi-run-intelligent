from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.analytics.domain.value_objects.application_health_baseline import ApplicationHealthBaseline
from app.modules.ticket_management.domain.enums.application import Application


class HealthBaselineRepository(ABC):
	"""The cached per-application baseline, recomputed by the daily scheduled job and read by
	both the admin overview (all applications at once) and the reactive health check (one)."""

	@abstractmethod
	async def get(self, application: Application) -> ApplicationHealthBaseline | None:
		raise NotImplementedError

	@abstractmethod
	async def get_all(self) -> dict[Application, ApplicationHealthBaseline]:
		raise NotImplementedError

	@abstractmethod
	async def upsert(self, baseline: ApplicationHealthBaseline) -> None:
		raise NotImplementedError
