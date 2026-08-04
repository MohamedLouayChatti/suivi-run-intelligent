from __future__ import annotations

from pathlib import PurePosixPath
from uuid import UUID

from app.modules.ticket_management.domain.exceptions import AttachmentTooLarge, UnsupportedAttachmentType

MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = frozenset(
	{
		"image/png",
		"image/jpeg",
		"image/gif",
		"image/webp",
		"application/pdf",
		"application/msword",
		"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		"application/vnd.ms-excel",
		"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		"application/vnd.ms-powerpoint",
		"application/vnd.openxmlformats-officedocument.presentationml.presentation",
		"text/csv",
		"text/plain",
		# Browsers commonly send this for extensions they don't recognize (e.g. .log).
		"application/octet-stream",
	}
)


def validate_upload(content: bytes, content_type: str) -> None:
	if len(content) > MAX_ATTACHMENT_SIZE_BYTES:
		raise AttachmentTooLarge()
	if content_type not in ALLOWED_CONTENT_TYPES:
		raise UnsupportedAttachmentType()


def build_storage_path(scope: str, attachment_id: UUID, filename: str) -> str:
	extension = PurePosixPath(filename).suffix
	return f"attachments/{scope}/{attachment_id}{extension}"
