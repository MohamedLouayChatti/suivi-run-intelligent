from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.knowledge_base.domain.enums.knowledge_source_type import KnowledgeSourceType
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.database.base import Base


class KnowledgeItemModel(Base):
	"""pgvector Vector column lives only here.
	Vector dimension is left unconstrained until an embedding model is chosen; fixing it and
	adding the actual HNSW/IVFFlat index is a follow-up migration once that decision is made.

	`application` reuses Ticket Management's existing `ticket_application` Postgres enum type
	(same Python Application enum) rather than declaring a second, duplicate native type.
	"""

	__tablename__ = "knowledge_items"
	__table_args__ = (
		Index("ix_knowledge_items_source_id", "source_id"),
		Index("ix_knowledge_items_application", "application"),
	)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	source_type: Mapped[KnowledgeSourceType] = mapped_column(
		SAEnum(KnowledgeSourceType, name="knowledge_source_type"), nullable=False,
	)
	source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	application: Mapped[Application] = mapped_column(
		SAEnum(Application, name="ticket_application"), nullable=False,
	)
	embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)
	embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
	embedding_model_version: Mapped[str] = mapped_column(String(50), nullable=False)
	generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
