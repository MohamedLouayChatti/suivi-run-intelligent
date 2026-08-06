from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.notifications.domain.enums.notification_type import NotificationType
from app.shared.database.base import Base


class NotificationModel(Base):
	__tablename__ = "notifications"
	__table_args__ = (
		Index("ix_notifications_recipient_id", "recipient_id"),
		Index("ix_notifications_created_at", "created_at"),
		Index("ix_notifications_type", "type"),
	)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	recipient_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	message: Mapped[str] = mapped_column(Text, nullable=False)
	type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType, name="notification_type"), nullable=False)
	action: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
	# Column is named "metadata" in the database; the Python attribute can't share
	# that name -- SQLAlchemy's DeclarativeBase already reserves `metadata` for the
	# schema's own MetaData object.
	notification_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
