from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.interfaces.notification_read_repository import NotificationReadRepository
from app.modules.notifications.application.queries.list_notifications.query import ListNotificationsQuery
from app.modules.notifications.infrastructure.persistence import mapper
from app.modules.notifications.infrastructure.persistence.models.notification_model import NotificationModel


class SqlAlchemyNotificationReadRepository(NotificationReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_notification(self, notification_id: UUID) -> NotificationDTO | None:
		model = await self.session.scalar(select(NotificationModel).where(NotificationModel.id == notification_id))
		if model is None:
			return None
		return mapper.model_to_dto(model)

	async def list_notifications(self, query: ListNotificationsQuery) -> list[NotificationDTO]:
		stmt = select(NotificationModel).where(NotificationModel.recipient_id == query.recipient_id)
		if query.unread_only:
			stmt = stmt.where(NotificationModel.read_at.is_(None))
		stmt = stmt.order_by(NotificationModel.created_at.desc()).limit(query.limit).offset(query.offset)
		result = await self.session.scalars(stmt)
		return [mapper.model_to_dto(model) for model in result.all()]

	async def count_unread(self, recipient_id: UUID) -> int:
		stmt = select(func.count()).select_from(NotificationModel).where(
			NotificationModel.recipient_id == recipient_id, NotificationModel.read_at.is_(None)
		)
		return await self.session.scalar(stmt) or 0
