from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListNotificationsQuery:
	recipient_id: UUID
	unread_only: bool = False
	limit: int = 100
	offset: int = 0
