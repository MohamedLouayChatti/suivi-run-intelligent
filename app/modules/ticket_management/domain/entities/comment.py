from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.exceptions import CommentDeleted, EmptyComment, DuplicateAttachment


@dataclass
class Comment:
	id: UUID
	author_id: UUID
	content: str
	created_at: datetime
	attachments: list[Attachment] = field(default_factory=list)
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

	def add_attachment(self, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_not_deleted()
		if any(existing.id == attachment.id for existing in self.attachments):
			raise DuplicateAttachment()
		self.attachments.append(attachment)
		self.updated_at = added_at
