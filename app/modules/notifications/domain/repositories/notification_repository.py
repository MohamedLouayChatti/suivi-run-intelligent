from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.modules.notifications.domain.entities.notification import Notification


class NotificationRepository(ABC):
	@abstractmethod
	async def add(self, notification: Notification) -> None:
		raise NotImplementedError

	@abstractmethod
	async def get(self, notification_id: UUID) -> Notification | None:
		raise NotImplementedError

	@abstractmethod
	async def save(self, notification: Notification) -> None:
		raise NotImplementedError

	@abstractmethod
	async def mark_all_read(self, recipient_id: UUID, read_at: datetime) -> int:
		"""Bulk-set read_at for every unread notification belonging to recipient_id.

		A direct UPDATE, not a load-mutate-save loop over N aggregates: there is no
		invariant beyond "set read_at" that requires loading each entity first.
		Returns the number of rows updated.
		"""
		raise NotImplementedError
