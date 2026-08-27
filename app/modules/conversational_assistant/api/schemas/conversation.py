from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.conversational_assistant.application.dto.conversation_summary_dto import ConversationSummaryDTO


class CreateConversationResponse(BaseModel):
	id: UUID
	created_at: datetime

	@classmethod
	def from_dto(cls, dto: ConversationSummaryDTO) -> CreateConversationResponse:
		return cls(id=dto.id, created_at=dto.created_at)


class ConversationSummaryResponse(BaseModel):
	id: UUID
	title: str | None
	created_at: datetime
	updated_at: datetime

	@classmethod
	def from_dto(cls, dto: ConversationSummaryDTO) -> ConversationSummaryResponse:
		return cls(id=dto.id, title=dto.title, created_at=dto.created_at, updated_at=dto.updated_at)
