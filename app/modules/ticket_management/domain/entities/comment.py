from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.exceptions import CommentDeleted, EmptyComment


@dataclass
class Comment:
	id: UUID
	author_id: UUID
	content: str
	created_at: datetime
	edited_at: datetime | None = None
	deleted_at: datetime | None = None

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		author_id: UUID,
		content: str,
		created_at: datetime,
	) -> Comment:
		if not content.strip():
			raise EmptyComment()
		return cls(
			id=id,
			author_id=author_id,
			content=content,
			created_at=created_at,
			deleted_at=None
		)
	
	def _ensure_not_deleted(self) -> None:
		if self.deleted_at is not None:
			raise CommentDeleted()
	
	def delete(self, deleted_at: datetime) -> None:
		self._ensure_not_deleted()
		self.deleted_at = deleted_at

	def edit(self, content: str, edited_at: datetime) -> None:
		self._ensure_not_deleted()
		if not content.strip():
			raise EmptyComment()
		self.content = content
		self.edited_at = edited_at
