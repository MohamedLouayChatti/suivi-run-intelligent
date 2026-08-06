from __future__ import annotations

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.interfaces.notification_read_repository import NotificationReadRepository
from app.modules.notifications.application.queries.list_notifications.query import ListNotificationsQuery


class ListNotificationsHandler:
	def __init__(self, read_repository: NotificationReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: ListNotificationsQuery) -> list[NotificationDTO]:
		return await self.read_repository.list_notifications(query)
