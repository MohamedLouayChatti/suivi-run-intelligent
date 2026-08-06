from __future__ import annotations

from app.modules.notifications.application.interfaces.notification_read_repository import NotificationReadRepository
from app.modules.notifications.application.queries.count_unread_notifications.query import CountUnreadNotificationsQuery


class CountUnreadNotificationsHandler:
	def __init__(self, read_repository: NotificationReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: CountUnreadNotificationsQuery) -> int:
		return await self.read_repository.count_unread(query.recipient_id)
