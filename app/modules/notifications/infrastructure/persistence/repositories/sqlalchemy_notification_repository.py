from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.domain.entities.notification import Notification
from app.modules.notifications.domain.repositories.notification_repository import NotificationRepository
from app.modules.notifications.infrastructure.persistence import mapper
from app.modules.notifications.infrastructure.persistence.models.notification_model import NotificationModel


class SqlAlchemyNotificationRepository(NotificationRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, notification: Notification) -> None:
		self.session.add(mapper.notification_to_model(notification))

	async def get(self, notification_id: UUID) -> Notification | None:
		model = await self.session.scalar(select(NotificationModel).where(NotificationModel.id == notification_id))
		if model is None:
			return None
		return mapper.model_to_domain(model)

	async def save(self, notification: Notification) -> None:
		model = await self.session.scalar(select(NotificationModel).where(NotificationModel.id == notification.id))
		if model is None:
			self.session.add(mapper.notification_to_model(notification))
			return
		mapper.sync_notification_model(model, notification)

	async def mark_all_read(self, recipient_id: UUID, read_at: datetime) -> int:
		stmt = (
			update(NotificationModel)
			.where(NotificationModel.recipient_id == recipient_id, NotificationModel.read_at.is_(None))
			.values(read_at=read_at)
		)
		result = await self.session.execute(stmt)
		return result.rowcount
