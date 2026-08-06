from __future__ import annotations

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.interfaces.notification_publisher import NotificationPublisher
from app.modules.notifications.infrastructure.delivery.sse_connection_manager import SSEConnectionManager


class SSENotificationPublisher(NotificationPublisher):
	"""The sole delivery adapter today. NotificationService depends only on the
	NotificationPublisher port, so a future channel (email, push) is an
	additional adapter, not a rewrite of the service."""

	def __init__(self, connection_manager: SSEConnectionManager) -> None:
		self._connection_manager = connection_manager

	async def publish(self, notification: NotificationDTO) -> None:
		self._connection_manager.publish(notification)
