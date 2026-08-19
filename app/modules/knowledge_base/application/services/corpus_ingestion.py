from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from app.modules.knowledge_base.application.exceptions import MixedEmbeddingCorpus
from app.modules.knowledge_base.domain.entities.knowledge_item import TicketKnowledgeItem
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.knowledge_base.domain.services.description_preprocessor import preprocess_description
from app.modules.ticket_management.application.dto.ticket_dto import TicketContentDTO
from app.shared.ai.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class CorpusIngestion:
	"""The single definition of how a ticket's text becomes a stored knowledge item.

	The counterpart of SimilarityComputation, which plays the same role for the graph, and it
	exists for the same reason: every bulk path that adds to the corpus -- the backfill over
	historical tickets, and a batch import of a file -- must represent a ticket identically, or the
	corpus ends up holding vectors that were produced from subtly different text and nothing
	afterwards can tell which is which. Same preprocessing, same provider, same entity, so a ticket
	that arrives one way and a ticket that arrives the other are indistinguishable once stored.

	Embeds, unlike SimilarityComputation, because that is precisely the difference between adding
	to the corpus and deriving from it.
	"""

	def __init__(self, embedding_provider: EmbeddingProvider) -> None:
		self.embedding_provider = embedding_provider

	async def prepare(self, knowledge_items: KnowledgeItemRepository) -> None:
		"""Everything that must be true before a pass embeds anything, checked while it is still
		free to stop.

		`warm_up` resolves the model and fails immediately if the provider is unreachable or
		serving a build other than the pinned one, rather than in the twentieth minute of a run --
		and it is also what makes the model name and version below readable at all.

		The corpus check catches the one corruption that hides itself: vectors from two models
		occupy unrelated coordinate spaces, so a graph spanning both is structurally valid, passes
		every constraint, and is quietly meaningless. It cannot be detected after the fact, which
		is why it is checked before rather than repaired after.
		"""
		await self.embedding_provider.warm_up()
		present = await knowledge_items.distinct_model_versions()
		expected = (self.embedding_provider.model_name, self.embedding_provider.model_version)
		if any(pair != expected for pair in present):
			raise MixedEmbeddingCorpus(present, expected)

	async def item_for(self, ticket: TicketContentDTO, generated_at: datetime) -> TicketKnowledgeItem | None:
		"""The knowledge item for one ticket, or None when there is nothing left to embed.

		Preprocessing can empty a description outright -- one consisting only of an order reference
		becomes a bare placeholder. Embedding that would store a vector for "a commande was
		mentioned", which is a near neighbour of every other such ticket and of nothing meaningful,
		so the ticket is left without a knowledge item instead. A later pass picks it up for free
		if it ever gains real text.
		"""
		preprocessed = preprocess_description(ticket.description)
		if not preprocessed.embedding_text.strip():
			logger.debug("Skipping ticket %s: nothing left to embed after preprocessing", ticket.id)
			return None

		embedding = await self.embedding_provider.embed(preprocessed.embedding_text)
		return TicketKnowledgeItem.create(
			id=uuid4(),
			source_id=ticket.id,
			application=ticket.application,
			embedding=embedding,
			embedding_model=self.embedding_provider.model_name,
			embedding_model_version=self.embedding_provider.model_version,
			generated_at=generated_at,
			identifiers=list(preprocessed.identifiers),
			genergy_id=ticket.genergy_id,
			oceane_id=ticket.oceane_id,
		)
