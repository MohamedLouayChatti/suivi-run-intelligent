from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.modules.notifications.domain.enums.notification_type import NotificationType
from app.modules.notifications.domain.value_objects.notification_action import NotificationAction


@dataclass
class Notification:
	id: UUID
	recipient_id: UUID
	title: str
	message: str
	type: NotificationType
	action: NotificationAction | None
	created_at: datetime
	read_at: datetime | None = None
	metadata: dict[str, Any] = field(default_factory=dict)

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		recipient_id: UUID,
		title: str,
		message: str,
		type: NotificationType,
		action: NotificationAction | None,
		created_at: datetime,
		metadata: dict[str, Any] | None = None,
	) -> Notification:
		return cls(
			id=id,
			recipient_id=recipient_id,
			title=title,
			message=message,
			type=type,
			action=action,
			created_at=created_at,
			metadata=metadata or {},
		)

	def mark_read(self, read_at: datetime) -> None:
		"""Unread -> Read. Idempotent: re-marking an already-read notification keeps
		its original read_at rather than raising -- there is no ordering invariant a
		second read event could violate."""
		if self.read_at is None:
			self.read_at = read_at
