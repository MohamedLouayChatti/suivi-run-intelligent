from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.exceptions import NotificationNotFound
from app.modules.notifications.application.interfaces.notification_publisher import NotificationPublisher
from app.modules.notifications.application.interfaces.unit_of_work import UnitOfWork
from app.modules.notifications.domain.entities.notification import Notification


class NotificationService:
	"""Persists and delivers notifications; knows nothing about the domain events
	that produced them -- it only ever works with Notification aggregates."""

	def __init__(self, uow: UnitOfWork, publisher: NotificationPublisher) -> None:
		self.uow = uow
		self.publisher = publisher

	async def create(self, notification: Notification) -> None:
		await self.uow.notifications.add(notification)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.publisher.publish(NotificationDTO.from_notification(notification))

	async def mark_read(self, notification_id: UUID, read_at: datetime) -> Notification:
		notification = await self.uow.notifications.get(notification_id)
		if notification is None:
			raise NotificationNotFound()
		notification.mark_read(read_at)
		await self.uow.notifications.save(notification)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		return notification

	async def mark_all_read(self, recipient_id: UUID, read_at: datetime) -> int:
		count = await self.uow.notifications.mark_all_read(recipient_id, read_at)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		return count
