from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class EditCommentCommand:
	ticket_id: UUID
	comment_id: UUID
	content: str
	edited_at: datetime
	actor_id: UUID
