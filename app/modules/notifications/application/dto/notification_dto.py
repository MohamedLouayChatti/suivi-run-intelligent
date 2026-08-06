from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.modules.notifications.domain.entities.notification import Notification
from app.modules.notifications.domain.enums.notification_type import NotificationType
from app.modules.notifications.domain.value_objects.notification_action import NotificationAction


@dataclass(frozen=True)
class NotificationDTO:
	id: UUID
	recipient_id: UUID
	title: str
	message: str
	type: NotificationType
	action: NotificationAction | None
	created_at: datetime
	read_at: datetime | None
	metadata: dict[str, Any] = field(default_factory=dict)

	@classmethod
	def from_notification(cls, notification: Notification) -> NotificationDTO:
		return cls(
			id=notification.id,
			recipient_id=notification.recipient_id,
			title=notification.title,
			message=notification.message,
			type=notification.type,
			action=notification.action,
			created_at=notification.created_at,
			read_at=notification.read_at,
			metadata=notification.metadata,
		)
