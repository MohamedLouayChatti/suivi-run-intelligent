from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel

from app.shared.database.base import Base


class AttachmentModel(Base):
	__tablename__ = "ticket_attachments"
	__table_args__ = (
		CheckConstraint(
			"(ticket_id IS NOT NULL AND comment_id IS NULL) OR (ticket_id IS NULL AND comment_id IS NOT NULL)",
			name="ck_ticket_attachments_single_parent",
		),
	)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	ticket_id: Mapped[UUID | None] = mapped_column(
		PGUUID(as_uuid=True),
		ForeignKey("tickets.id", ondelete="CASCADE"),
		nullable=True,
	)
	comment_id: Mapped[UUID | None] = mapped_column(
		PGUUID(as_uuid=True),
		ForeignKey("ticket_comments.id", ondelete="CASCADE"),
		nullable=True,
	)
	filename: Mapped[str] = mapped_column(String(255), nullable=False)
	content_type: Mapped[str] = mapped_column(String(255), nullable=False)
	storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
	uploaded_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	ticket: Mapped[TicketModel | None] = relationship(
		back_populates="attachments",
		foreign_keys=[ticket_id],
	)
	comment: Mapped[CommentModel | None] = relationship(
		back_populates="attachments",
		foreign_keys=[comment_id],
	)
