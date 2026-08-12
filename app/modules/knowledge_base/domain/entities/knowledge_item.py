from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.knowledge_base.domain.enums.knowledge_source_type import KnowledgeSourceType
from app.modules.ticket_management.domain.enums.application import Application


@dataclass
class KnowledgeItem:
	"""A source-agnostic embeddable unit of knowledge. V1: one per ticket, embedding its
	description only. Framework-free: `embedding` is a plain
	list[float], never a pgvector-specific type (that conversion is Infrastructure's concern).

	`application` denormalizes Ticket Management's Application enum so
	candidate search can filter without joining another module's table -- safe to treat as fixed
	for a ticket's lifetime now that TransferApplicationCommand (the only path that could have
	changed it) has been removed as dead code.
	"""

	id: UUID
	source_type: KnowledgeSourceType
	source_id: UUID
	application: Application
	embedding: list[float]
	embedding_model: str
	embedding_model_version: str
	generated_at: datetime

	@classmethod
	def create(
		cls, *, id: UUID, source_type: KnowledgeSourceType, source_id: UUID,
		application: Application, embedding: list[float],
		embedding_model: str, embedding_model_version: str, generated_at: datetime,
	) -> KnowledgeItem:
		return cls(
			id=id, source_type=source_type, source_id=source_id, application=application,
			embedding=embedding, embedding_model=embedding_model,
			embedding_model_version=embedding_model_version, generated_at=generated_at,
		)
