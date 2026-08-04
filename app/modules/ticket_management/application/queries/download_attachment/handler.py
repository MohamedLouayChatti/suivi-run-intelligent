from __future__ import annotations

from app.modules.ticket_management.application.dto.attachment_content_dto import AttachmentContentDTO
from app.modules.ticket_management.application.exceptions import AttachmentNotFound
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.download_attachment.query import DownloadAttachmentQuery
from app.shared.storage.service import StorageService


class DownloadAttachmentHandler:
	def __init__(self, read_repository: TicketReadRepository, storage_service: StorageService) -> None:
		self.read_repository = read_repository
		self.storage_service = storage_service

	async def handle(self, query: DownloadAttachmentQuery) -> AttachmentContentDTO:
		attachment = await self.read_repository.get_attachment(query.attachment_id)
		if attachment is None or attachment.deleted_at is not None:
			raise AttachmentNotFound()
		content = await self.storage_service.read(attachment.storage_path)
		return AttachmentContentDTO(
			filename=attachment.filename,
			content_type=attachment.content_type,
			content=content,
		)
