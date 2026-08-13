from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.knowledge_base.domain.enums.knowledge_source_type import KnowledgeSourceType
from app.modules.knowledge_base.domain.services.description_preprocessor import ExtractedIdentifier
from app.modules.ticket_management.domain.enums.application import Application


@dataclass
class KnowledgeItem:
	"""A source-agnostic embeddable unit of knowledge -- the abstraction every knowledge source
	shares. Tickets are the first source (see `TicketKnowledgeItem`); application documentation,
	which the conversational assistant will retrieve over, is the next one, and it will carry a
	completely different set of source-specific fields.

	Only what is genuinely common to every source lives here. Framework-free: `embedding` is a
	plain list[float], never a pgvector-specific type (that conversion is Infrastructure's
	concern).

	`application` stays on the base rather than on the ticket subtype because scoping knowledge
	by application is common to every source -- documentation is per-application too -- and
	because keeping it here lets candidate search filter with a plain indexed predicate instead
	of joining the subtype table on the hot retrieval path.

	`identifiers` holds what `preprocess_description` lifted out of the source text before
	embedding it. They are stripped from the embedded text precisely so they cannot distort
	semantic similarity, and kept here so exact retrieval can still use them.
	"""

	id: UUID
	source_type: KnowledgeSourceType
	source_id: UUID
	application: Application
	embedding: list[float]
	embedding_model: str
	embedding_model_version: str
	generated_at: datetime
	identifiers: list[ExtractedIdentifier] = field(default_factory=list)


@dataclass
class TicketKnowledgeItem(KnowledgeItem):
	"""A KnowledgeItem whose source is a ticket.

	`genergy_id` is denormalized from Ticket Management for the same reason `application` is:
	so retrieval can resolve a reference without joining another module's table. It is what makes
	hybrid retrieval work at all -- when a description says "suite ticket INC001010948992", the
	ticket being referenced does not repeat that string in its own description, it *is* the
	ticket whose genergy_id equals it. Matching descriptions against each other would miss the
	link entirely.
	"""

	genergy_id: str | None = None
	oceane_id: str | None = None

	@classmethod
	def create(
		cls, *, id: UUID, source_id: UUID, application: Application, embedding: list[float],
		embedding_model: str, embedding_model_version: str, generated_at: datetime,
		identifiers: list[ExtractedIdentifier] | None = None,
		genergy_id: str | None = None, oceane_id: str | None = None,
	) -> TicketKnowledgeItem:
		return cls(
			id=id, source_type=KnowledgeSourceType.TICKET, source_id=source_id,
			application=application, embedding=embedding, embedding_model=embedding_model,
			embedding_model_version=embedding_model_version, generated_at=generated_at,
			identifiers=list(identifiers or []), genergy_id=genergy_id, oceane_id=oceane_id,
		)
