from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class CommentAdded(DomainEvent):
	ticket_id: UUID
	comment_id: UUID
	author_id: UUID
	created_at: datetime
	actor_id: UUID
