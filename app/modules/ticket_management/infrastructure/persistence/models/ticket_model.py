from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
    from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import AttachmentModel

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.shared.database.base import Base


class TicketModel(Base):
	__tablename__ = "tickets"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	application: Mapped[Application] = mapped_column(SAEnum(Application, name="ticket_application"), nullable=False)
	status: Mapped[Status] = mapped_column(SAEnum(Status, name="ticket_status"), nullable=False)
	priority: Mapped[Priority] = mapped_column(SAEnum(Priority, name="ticket_priority"), nullable=False)
	assignee_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	pending_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
	resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
	archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	comments: Mapped[list["CommentModel"]] = relationship(
		back_populates="ticket",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
	)
	attachments: Mapped[list["AttachmentModel"]] = relationship(
		back_populates="ticket",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
		foreign_keys="AttachmentModel.ticket_id",
	)
