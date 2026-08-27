from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.conversational_assistant.application.dto.conversation_messages_dto import ConversationMessagesDTO
from app.modules.conversational_assistant.application.dto.conversation_summary_dto import ConversationSummaryDTO
from app.modules.conversational_assistant.application.interfaces.conversation_read_repository import (
	ConversationReadRepository,
)
from app.modules.conversational_assistant.infrastructure.persistence import mapper
from app.modules.conversational_assistant.infrastructure.persistence.models.conversation_model import (
	ConversationModel,
)
from app.modules.conversational_assistant.infrastructure.persistence.models.message_model import MessageModel
from app.modules.conversational_assistant.infrastructure.persistence.models.run_model import RunModel
from app.shared.pagination import Page


class SqlAlchemyConversationReadRepository(ConversationReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_owner(self, conversation_id: UUID) -> UUID | None:
		stmt = select(ConversationModel.user_id).where(ConversationModel.id == conversation_id)
		return await self.session.scalar(stmt)

	async def get_run_owner(self, run_id: UUID) -> UUID | None:
		stmt = (
			select(ConversationModel.user_id)
			.join(RunModel, RunModel.conversation_id == ConversationModel.id)
			.where(RunModel.id == run_id)
		)
		return await self.session.scalar(stmt)

	async def get_messages(
		self, conversation_id: UUID, *, limit: int, offset: int
	) -> ConversationMessagesDTO | None:
		owner_id = await self.get_owner(conversation_id)
		if owner_id is None:
			return None

		total = await self.session.scalar(
			select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id == conversation_id)
		)
		page_stmt = (
			select(MessageModel)
			.where(MessageModel.conversation_id == conversation_id)
			.order_by(MessageModel.created_at)
			.limit(limit)
			.offset(offset)
		)
		message_models = (await self.session.scalars(page_stmt)).all()

		latest_run_stmt = (
			select(RunModel)
			.where(RunModel.conversation_id == conversation_id)
			.order_by(RunModel.started_at.desc())
			.limit(1)
		)
		latest_run_model = await self.session.scalar(latest_run_stmt)

		return ConversationMessagesDTO(
			messages=Page(
				items=[mapper.message_model_to_dto(message_model) for message_model in message_models],
				total=total or 0,
			),
			latest_run=None if latest_run_model is None else mapper.run_model_to_summary_dto(latest_run_model),
		)

	async def list_conversations(self, user_id: UUID, *, limit: int, offset: int) -> Page[ConversationSummaryDTO]:
		total = await self.session.scalar(
			select(func.count()).select_from(ConversationModel).where(ConversationModel.user_id == user_id)
		)
		stmt = (
			select(ConversationModel)
			.where(ConversationModel.user_id == user_id)
			.order_by(ConversationModel.updated_at.desc())
			.limit(limit)
			.offset(offset)
		)
		conversation_models = (await self.session.scalars(stmt)).all()
		return Page(
			items=[mapper.conversation_model_to_summary_dto(model) for model in conversation_models],
			total=total or 0,
		)
