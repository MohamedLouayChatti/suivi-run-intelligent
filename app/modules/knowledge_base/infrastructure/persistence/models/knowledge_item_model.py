from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.knowledge_base.domain.enums.identifier_type import IdentifierType
from app.modules.knowledge_base.domain.enums.knowledge_source_type import KnowledgeSourceType
from app.modules.knowledge_base.infrastructure.embedding_model import EMBEDDING_DIMENSIONS
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.database.base import Base


class KnowledgeItemModel(Base):
	"""Base table of the joined-table inheritance hierarchy, discriminated by `source_type`.

	Everything shared by all knowledge sources lives here -- crucially the vector column, so the
	ANN index stays on a single table and semantic search never has to join a subtype to run.
	Source-specific columns live in the subtype tables (`ticket_knowledge_items` today,
	documentation next), which is what keeps a Document from ever carrying a ticket's genergy_id.

	pgvector Vector column lives only here, pinned to the chosen model's dimension: pgvector
	requires a fixed width to build an ANN index at all, and a declared width is also what makes a
	wrong-model insert fail loudly at the database instead of silently corrupting the corpus. The
	HNSW index over this column is created in migration a4f61c8b7e05.

	`application` reuses Ticket Management's existing `ticket_application` Postgres enum type
	(same Python Application enum) rather than declaring a second, duplicate native type.
	"""

	__tablename__ = "knowledge_items"
	__table_args__ = (
		Index("ix_knowledge_items_source_id", "source_id"),
		Index("ix_knowledge_items_application", "application"),
		# HNSW rather than IVFFlat: IVFFlat has to be built against an already-populated table and
		# re-tuned as the corpus grows, while HNSW is built incrementally and needs no such
		# maintenance -- which matters for a table that starts at one backfill and then grows one
		# ticket at a time. `vector_cosine_ops` must match the operator the search port queries
		# with (`cosine_distance`, i.e. `<=>`); an index built for a different metric is simply
		# never used. m/ef_construction are pgvector's defaults, stated explicitly so a rebuild
		# reproduces the same index rather than inheriting whatever a future default becomes.
		Index(
			"ix_knowledge_items_embedding_hnsw",
			"embedding",
			postgresql_using="hnsw",
			postgresql_ops={"embedding": "vector_cosine_ops"},
			postgresql_with={"m": 16, "ef_construction": 64},
		),
	)
	__mapper_args__ = {"polymorphic_on": "source_type"}

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	source_type: Mapped[KnowledgeSourceType] = mapped_column(
		SAEnum(KnowledgeSourceType, name="knowledge_source_type"), nullable=False,
	)
	source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	application: Mapped[Application] = mapped_column(
		SAEnum(Application, name="ticket_application"), nullable=False,
	)
	embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
	embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
	embedding_model_version: Mapped[str] = mapped_column(String(50), nullable=False)
	generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

	identifiers: Mapped[list["KnowledgeItemIdentifierModel"]] = relationship(
		back_populates="knowledge_item", cascade="all, delete-orphan", lazy="selectin",
	)


class TicketKnowledgeItemModel(KnowledgeItemModel):
	"""Ticket-specific half of a knowledge item.

	`genergy_id` is indexed because it is the right-hand side of every reference lookup: a
	description citing "INC001010948992" is resolved against this column, not against other
	descriptions.
	"""

	__tablename__ = "ticket_knowledge_items"
	__table_args__ = (Index("ix_ticket_knowledge_items_genergy_id", "genergy_id"),)
	__mapper_args__ = {"polymorphic_identity": KnowledgeSourceType.TICKET}

	id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True), ForeignKey("knowledge_items.id", ondelete="CASCADE"), primary_key=True,
	)
	genergy_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
	oceane_id: Mapped[str | None] = mapped_column(String(50), nullable=True)


class KnowledgeItemIdentifierModel(Base):
	"""One identifier extracted from a knowledge item's source text.

	A normalized child table rather than JSONB because these rows exist to be *queried by
	content* -- "which items carry this value of this type" -- which is the opposite of the
	opaque-payload use JSONB serves elsewhere in this codebase (audit_entries.payload,
	notifications.metadata). The composite (value, identifier_type) index is what the reference
	lookup rides on.
	"""

	__tablename__ = "knowledge_item_identifiers"
	__table_args__ = (
		Index("ix_knowledge_item_identifiers_value_type", "value", "identifier_type"),
		Index("ix_knowledge_item_identifiers_item_id", "knowledge_item_id"),
	)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	knowledge_item_id: Mapped[UUID] = mapped_column(
		PGUUID(as_uuid=True), ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False,
	)
	identifier_type: Mapped[IdentifierType] = mapped_column(
		SAEnum(IdentifierType, name="knowledge_identifier_type"), nullable=False,
	)
	value: Mapped[str] = mapped_column(String(100), nullable=False)

	knowledge_item: Mapped[KnowledgeItemModel] = relationship(back_populates="identifiers")
