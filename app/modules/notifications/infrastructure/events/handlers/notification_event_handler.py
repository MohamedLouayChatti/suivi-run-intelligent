from __future__ import annotations

from collections.abc import Callable

from app.modules.notifications.application.interfaces.notification_publisher import NotificationPublisher
from app.modules.notifications.application.interfaces.unit_of_work import UnitOfWork
from app.modules.notifications.application.mapping.notification_mapper import NotificationMapper
from app.modules.notifications.application.services.notification_service import NotificationService
from app.shared.events.event import DomainEvent
from app.shared.events.handler import EventHandler


class NotificationEventHandler(EventHandler):
	"""Thin consumer: delegates translation to NotificationMapper, persists and
	delivers each resulting Notification through NotificationService.

	Receives a fresh Unit of Work per call (via `uow_factory`) rather than one
	held for the handler's lifetime, since the same handler instance is
	subscribed to every notified event type and reused across concurrent
	requests -- one shared session would not be safe for that. Reused across
	every Notification produced by a single event (e.g. a broadcast), then
	closed once, since they all belong to the same handling of one event.
	"""

	def __init__(self, uow_factory: Callable[[], UnitOfWork], mapper: NotificationMapper, publisher: NotificationPublisher) -> None:
		self.uow_factory = uow_factory
		self.mapper = mapper
		self.publisher = publisher

	async def handle(self, event: DomainEvent) -> None:
		notifications = await self.mapper.to_notifications(event)
		if not notifications:
			return
		uow = self.uow_factory()
		service = NotificationService(uow, self.publisher)
		try:
			for notification in notifications:
				await service.create(notification)
		finally:
			await uow.close()
