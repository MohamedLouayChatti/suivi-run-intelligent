from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListConversationsQuery:
	user_id: UUID
	limit: int = 50
	offset: int = 0
