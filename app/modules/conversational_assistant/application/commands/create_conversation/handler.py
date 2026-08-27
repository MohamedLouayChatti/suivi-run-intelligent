from __future__ import annotations

from app.modules.conversational_assistant.application.commands.create_conversation.command import (
	CreateConversationCommand,
)
from app.modules.conversational_assistant.application.dto.conversation_summary_dto import ConversationSummaryDTO
from app.modules.conversational_assistant.application.interfaces.unit_of_work import UnitOfWork
from app.modules.conversational_assistant.domain.entities.conversation import Conversation


class CreateConversationHandler:
	def __init__(self, uow: UnitOfWork) -> None:
		self.uow = uow

	async def handle(self, command: CreateConversationCommand) -> ConversationSummaryDTO:
		conversation = Conversation.start(
			id=command.conversation_id, user_id=command.user_id, created_at=command.created_at,
		)
		await self.uow.conversations.add(conversation)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		return ConversationSummaryDTO.from_conversation(conversation)
