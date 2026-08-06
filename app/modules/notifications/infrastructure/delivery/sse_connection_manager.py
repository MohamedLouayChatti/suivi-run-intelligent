from __future__ import annotations

import asyncio
from uuid import UUID

from app.modules.notifications.application.dto.notification_dto import NotificationDTO


class SSEConnectionManager:
	"""In-process registry of live SSE connections, keyed by recipient.

	Single-process, in-memory -- same constraint every other part of this
	system's event bus already has (see InMemoryEventBus/SubscriptionRegistry).
	A recipient can hold more than one queue at once (multiple open tabs/devices).
	"""

	def __init__(self) -> None:
		self._connections: dict[UUID, list[asyncio.Queue[NotificationDTO]]] = {}

	def connect(self, recipient_id: UUID) -> asyncio.Queue[NotificationDTO]:
		queue: asyncio.Queue[NotificationDTO] = asyncio.Queue()
		self._connections.setdefault(recipient_id, []).append(queue)
		return queue

	def disconnect(self, recipient_id: UUID, queue: asyncio.Queue[NotificationDTO]) -> None:
		queues = self._connections.get(recipient_id)
		if not queues:
			return
		try:
			queues.remove(queue)
		except ValueError:
			return
		if not queues:
			del self._connections[recipient_id]

	def publish(self, notification: NotificationDTO) -> None:
		for queue in self._connections.get(notification.recipient_id, []):
			queue.put_nowait(notification)


connection_manager = SSEConnectionManager()
