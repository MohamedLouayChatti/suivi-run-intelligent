from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.mapping.action_serialization import serialize_action
from app.modules.notifications.domain.enums.notification_type import NotificationType


class NotificationResponse(BaseModel):
	id: UUID
	recipient_id: UUID
	title: str
	message: str
	type: NotificationType
	action: dict[str, Any] | None
	metadata: dict[str, Any]
	created_at: datetime
	read_at: datetime | None

	@classmethod
	def from_dto(cls, notification: NotificationDTO) -> NotificationResponse:
		return cls(
			id=notification.id,
			recipient_id=notification.recipient_id,
			title=notification.title,
			message=notification.message,
			type=notification.type,
			action=serialize_action(notification.action),
			metadata=notification.metadata,
			created_at=notification.created_at,
			read_at=notification.read_at,
		)


class UnreadCountResponse(BaseModel):
	count: int


class MarkAllReadResponse(BaseModel):
	marked_read: int
