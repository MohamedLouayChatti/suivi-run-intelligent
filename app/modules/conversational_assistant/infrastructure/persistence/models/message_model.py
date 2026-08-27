from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.conversational_assistant.domain.enums.message_role import MessageRole
from app.shared.database.base import Base

if TYPE_CHECKING:
	from app.modules.conversational_assistant.infrastructure.persistence.models.conversation_model import (
		ConversationModel,
	)


class MessageModel(Base):
	__tablename__ = "conversation_messages"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	conversation_id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False,
	)
	role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="conversation_message_role"), nullable=False)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

	conversation: Mapped["ConversationModel"] = relationship(back_populates="messages")
