from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.notifications.application.dto.notification_dto import NotificationDTO


class NotificationPublisher(ABC):
	"""Port for pushing a persisted notification to connected clients.

	NotificationService depends only on this abstraction, never on SSE directly --
	a future delivery channel (email, push) is an additional adapter, not a rewrite.
	"""

	@abstractmethod
	async def publish(self, notification: NotificationDTO) -> None:
		raise NotImplementedError
