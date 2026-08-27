from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database.base import Base

if TYPE_CHECKING:
	from app.modules.conversational_assistant.infrastructure.persistence.models.message_model import MessageModel
	from app.modules.conversational_assistant.infrastructure.persistence.models.run_model import RunModel


class ConversationModel(Base):
	__tablename__ = "conversations"
	__table_args__ = (Index("ix_conversations_user_id", "user_id"),)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	title: Mapped[str | None] = mapped_column(String(255), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

	messages: Mapped[list["MessageModel"]] = relationship(
		back_populates="conversation",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
		order_by="MessageModel.created_at",
	)
	runs: Mapped[list["RunModel"]] = relationship(
		back_populates="conversation",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
		order_by="RunModel.started_at",
	)
