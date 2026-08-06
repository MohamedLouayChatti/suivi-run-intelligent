from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.queries.list_notifications.query import ListNotificationsQuery


class NotificationReadRepository(ABC):
	@abstractmethod
	async def get_notification(self, notification_id: UUID) -> NotificationDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_notifications(self, query: ListNotificationsQuery) -> list[NotificationDTO]:
		raise NotImplementedError

	@abstractmethod
	async def count_unread(self, recipient_id: UUID) -> int:
		raise NotImplementedError
