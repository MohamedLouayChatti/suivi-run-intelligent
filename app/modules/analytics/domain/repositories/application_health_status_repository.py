from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.analytics.domain.value_objects.application_health_status import ApplicationHealthStatus
from app.modules.ticket_management.domain.enums.application import Application


class ApplicationHealthStatusRepository(ABC):
	"""The last known tier for each application -- read before a reactive check decides whether
	a new CRITICAL tier is a transition worth announcing, and written after every check."""

	@abstractmethod
	async def get(self, application: Application) -> ApplicationHealthStatus | None:
		raise NotImplementedError

	@abstractmethod
	async def upsert(self, status: ApplicationHealthStatus) -> None:
		raise NotImplementedError
