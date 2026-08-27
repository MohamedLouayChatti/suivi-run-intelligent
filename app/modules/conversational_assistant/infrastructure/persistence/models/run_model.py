from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.conversational_assistant.domain.enums.run_status import RunStatus
from app.shared.database.base import Base

if TYPE_CHECKING:
	from app.modules.conversational_assistant.infrastructure.persistence.models.conversation_model import (
		ConversationModel,
	)
	from app.modules.conversational_assistant.infrastructure.persistence.models.tool_invocation_model import (
		ToolInvocationModel,
	)


class RunModel(Base):
	__tablename__ = "conversation_runs"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	conversation_id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False,
	)
	triggering_message_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	response_message_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
	status: Mapped[RunStatus] = mapped_column(SAEnum(RunStatus, name="conversation_run_status"), nullable=False)
	started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
	failure_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

	conversation: Mapped["ConversationModel"] = relationship(back_populates="runs")
	tool_invocations: Mapped[list["ToolInvocationModel"]] = relationship(
		back_populates="run",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
		order_by="ToolInvocationModel.started_at",
	)
