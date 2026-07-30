from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.exceptions import (
	ChronologicalOrderViolation, CommentDeleted, DuplicateAttachment, EmptyComment,
)


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

	def _last_modified_at(self) -> datetime:
		return self.edited_at or self.created_at

	def _ensure_chronological(self, at: datetime) -> None:
		if at < self._last_modified_at():
			raise ChronologicalOrderViolation()

	def delete(self, deleted_at: datetime) -> None:
		self._ensure_not_deleted()
		self._ensure_chronological(deleted_at)
		self.deleted_at = deleted_at

	def edit(self, content: str, edited_at: datetime) -> None:
		self._ensure_not_deleted()
		self._ensure_chronological(edited_at)
		if not content.strip():
			raise EmptyComment()
		self.content = content
		self.edited_at = edited_at

	def add_attachment(self, attachment: Attachment, added_at: datetime) -> None:
		self._ensure_not_deleted()
		self._ensure_chronological(added_at)
		if any(existing.id == attachment.id for existing in self.attachments):
			raise DuplicateAttachment()
		self.attachments.append(attachment)
		self.edited_at = added_at
