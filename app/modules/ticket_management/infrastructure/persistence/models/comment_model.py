from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import AttachmentModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel

from app.shared.database.base import Base


class CommentModel(Base):
	__tablename__ = "ticket_comments"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	ticket_id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True),
		ForeignKey("tickets.id", ondelete="CASCADE"),
		nullable=False,
	)
	author_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	ticket: Mapped[TicketModel] = relationship(back_populates="comments")
	attachments: Mapped[list[AttachmentModel]] = relationship(
		back_populates="comment",
		cascade="all, delete-orphan",
		lazy="selectin",
		single_parent=True,
		foreign_keys="AttachmentModel.comment_id",
	)
