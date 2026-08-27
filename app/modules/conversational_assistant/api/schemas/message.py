from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.api.pagination import PagedResponse
from app.modules.conversational_assistant.application.dto.conversation_messages_dto import ConversationMessagesDTO
from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO
from app.modules.conversational_assistant.application.dto.run_summary_dto import RunSummaryDTO
from app.modules.conversational_assistant.application.dto.send_message_result_dto import SendMessageResultDTO
from app.modules.conversational_assistant.domain.enums.message_role import MessageRole
from app.modules.conversational_assistant.domain.enums.run_status import RunStatus


class SendMessageRequest(BaseModel):
	content: str = Field(min_length=1, max_length=8000)

	@field_validator("content")
	@classmethod
	def _content_not_blank(cls, value: str) -> str:
		if not value.strip():
			raise ValueError("Le message ne peut pas être vide.")
		return value


class SendMessageResponse(BaseModel):
	conversation_id: UUID
	user_message_id: UUID
	run_id: UUID

	@classmethod
	def from_dto(cls, dto: SendMessageResultDTO) -> SendMessageResponse:
		return cls(conversation_id=dto.conversation_id, user_message_id=dto.user_message_id, run_id=dto.run_id)


class MessageResponse(BaseModel):
	id: UUID
	role: MessageRole
	content: str
	created_at: datetime

	@classmethod
	def from_dto(cls, dto: MessageDTO) -> MessageResponse:
		return cls(id=dto.id, role=dto.role, content=dto.content, created_at=dto.created_at)


class RunSummaryResponse(BaseModel):
	id: UUID
	status: RunStatus
	failure_reason: str | None
	created_at: datetime

	@classmethod
	def from_dto(cls, dto: RunSummaryDTO) -> RunSummaryResponse:
		return cls(id=dto.id, status=dto.status, failure_reason=dto.failure_reason, created_at=dto.created_at)


class ConversationMessagesResponse(BaseModel):
	messages: PagedResponse[MessageResponse]
	latest_run: RunSummaryResponse | None

	@classmethod
	def from_dto(cls, dto: ConversationMessagesDTO) -> ConversationMessagesResponse:
		return cls(
			messages=PagedResponse(
				items=[MessageResponse.from_dto(message) for message in dto.messages.items],
				total=dto.messages.total,
			),
			latest_run=None if dto.latest_run is None else RunSummaryResponse.from_dto(dto.latest_run),
		)
