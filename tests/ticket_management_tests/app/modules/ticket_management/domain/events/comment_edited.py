from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CommentEdited:
	ticket_id: UUID
	comment_id: UUID
	edited_at: datetime
