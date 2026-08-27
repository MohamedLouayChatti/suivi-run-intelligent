from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database.base import Base

if TYPE_CHECKING:
	from app.modules.conversational_assistant.infrastructure.persistence.models.run_model import RunModel


class ToolInvocationModel(Base):
	__tablename__ = "conversation_tool_invocations"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	run_id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True), ForeignKey("conversation_runs.id", ondelete="CASCADE"), nullable=False,
	)
	tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
	arguments: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
	result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
	error: Mapped[str | None] = mapped_column(Text, nullable=True)
	started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

	run: Mapped["RunModel"] = relationship(back_populates="tool_invocations")
