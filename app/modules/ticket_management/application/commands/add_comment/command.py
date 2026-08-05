from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AddCommentCommand:
	ticket_id: UUID
	comment_id: UUID
	author_id: UUID
	content: str
	created_at: datetime
	actor_id: UUID
