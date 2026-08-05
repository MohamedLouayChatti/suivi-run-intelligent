from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base


class AuditEntryModel(Base):
	__tablename__ = "audit_entries"
	__table_args__ = (
		Index("ix_audit_entries_module", "module"),
		Index("ix_audit_entries_event_type", "event_type"),
		Index("ix_audit_entries_resource_type", "resource_type"),
		Index("ix_audit_entries_actor_id", "actor_id"),
		Index("ix_audit_entries_occurred_at", "occurred_at"),
	)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	module: Mapped[str] = mapped_column(String(100), nullable=False)
	event_type: Mapped[str] = mapped_column(String(150), nullable=False)
	action: Mapped[str] = mapped_column(String(150), nullable=False)
	resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
	actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
	payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
