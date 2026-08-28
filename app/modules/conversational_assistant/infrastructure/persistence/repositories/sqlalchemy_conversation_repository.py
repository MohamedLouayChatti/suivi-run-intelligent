from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.conversational_assistant.domain.entities.conversation import Conversation
from app.modules.conversational_assistant.domain.repositories.conversation_repository import ConversationRepository
from app.modules.conversational_assistant.infrastructure.persistence import mapper
from app.modules.conversational_assistant.infrastructure.persistence.models.conversation_model import (
	ConversationModel,
)
from app.modules.conversational_assistant.infrastructure.persistence.models.run_model import RunModel


class SqlAlchemyConversationRepository(ConversationRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, conversation: Conversation) -> None:
		self.session.add(mapper.conversation_to_model(conversation))

	async def get(self, conversation_id: UUID) -> Conversation | None:
		conversation_model = await self._load(conversation_id)
		if conversation_model is None:
			return None
		return mapper.conversation_model_to_domain(conversation_model)

	async def save(self, conversation: Conversation) -> None:
		conversation_model = await self._load(conversation.id)
		if conversation_model is None:
			self.session.add(mapper.conversation_to_model(conversation))
			return
		mapper.sync_conversation_model(conversation_model, conversation)

	async def set_title(self, conversation_id: UUID, title: str) -> None:
		# A statement, not a loaded model: the point of this method is that nothing about the
		# conversation is read into memory and written back, so there is no stale collection for a
		# concurrent agent run to lose. `synchronize_session=False` for the same reason -- there is
		# no identity map to keep in step here, this session loads nothing else.
		await self.session.execute(
			update(ConversationModel)
			.where(ConversationModel.id == conversation_id)
			.values(title=title)
			.execution_options(synchronize_session=False)
		)

	async def _load(self, conversation_id: UUID) -> ConversationModel | None:
		stmt = (
			select(ConversationModel)
			.where(ConversationModel.id == conversation_id)
			.options(
				selectinload(ConversationModel.messages),
				selectinload(ConversationModel.runs).selectinload(RunModel.tool_invocations),
			)
		)
		return await self.session.scalar(stmt)
