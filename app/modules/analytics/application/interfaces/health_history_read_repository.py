from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.analytics.application.dto.ticket_lifecycle_event_dto import TicketLifecycleEventDTO
from app.modules.ticket_management.domain.enums.application import Application


class HealthHistoryReadRepository(ABC):
	"""All-time history for one application, feeding the scheduled baseline job -- no window,
	unlike every other read repository in this module, because a baseline is deliberately
	computed over all available history rather than a bounded one."""

	@abstractmethod
	async def get_ticket_lifecycle_events(self, application: Application) -> list[TicketLifecycleEventDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_resolution_hours_history(self, application: Application) -> list[float]:
		raise NotImplementedError
