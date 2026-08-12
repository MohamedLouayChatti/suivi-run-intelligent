from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base


class SimilarityResultModel(Base):
	__tablename__ = "similarity_results"
	__table_args__ = (
		Index("ix_similarity_results_source_ticket_id", "source_ticket_id"),
		UniqueConstraint("source_ticket_id", "similar_ticket_id", name="uq_similarity_results_source_similar"),
	)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	source_ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	similar_ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
	similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
	rank: Mapped[int] = mapped_column(Integer, nullable=False)
	generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	embedding_model_version: Mapped[str] = mapped_column(String(50), nullable=False)
	algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
