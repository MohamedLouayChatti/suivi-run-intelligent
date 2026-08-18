from __future__ import annotations

from uuid import uuid4

from app.modules.knowledge_base.application.commands.generate_similarity_results.command import (
	GenerateSimilarityResultsCommand,
)
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.application.services.similarity_computation import SimilarityComputation
from app.modules.knowledge_base.domain.entities.knowledge_item import TicketKnowledgeItem
from app.modules.knowledge_base.domain.events.similarity_results_generated import SimilarityResultsGenerated
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.knowledge_base.domain.services.description_preprocessor import preprocess_description
from app.shared.ai.embedding_provider import EmbeddingProvider
from app.shared.events.event_publisher import EventPublisher


class GenerateSimilarityResultsHandler:
	"""Reacts to TicketCreated (via the infrastructure event handler): preprocess -> embed ->
	semantic + reference search -> rank -> persist -> publish. This handler only ever generates
	results for the one ticket it was triggered for; making the new ticket reachable *from* the
	older tickets it matched is the separate, one-hop concern of
	RefreshNeighborSimilarityHandler, which the same event handler runs immediately after this one.

	Ingestion and query preprocessing cannot drift here: this handler ingests the new ticket and
	queries with it in the same call, from the same single `preprocess_description` result.

	The two writes land in two different stores with no transaction between them, so their order is
	a deliberate choice rather than an accident of reading order. The knowledge item goes to the
	vector store first, and it is durable the moment it is written. If the graph write then fails,
	the ticket is in the corpus -- findable by every later search -- but has no results row of its
	own yet, which is a state the module already has a name for (a ticket with no match above the
	threshold looks identical) and which the rebuild pass repairs. The reverse order fails much
	worse: a ticket with results but no vector is permanently invisible to everyone else's
	searches, silently and with nothing to detect it.
	"""

	def __init__(
		self, uow: UnitOfWork, knowledge_items: KnowledgeItemRepository,
		embedding_provider: EmbeddingProvider, computation: SimilarityComputation,
		event_publisher: EventPublisher,
	) -> None:
		self.uow = uow
		self.knowledge_items = knowledge_items
		self.embedding_provider = embedding_provider
		self.computation = computation
		self.event_publisher = event_publisher

	async def handle(self, command: GenerateSimilarityResultsCommand) -> None:
		preprocessed = preprocess_description(command.description)
		embedding = await self.embedding_provider.embed(preprocessed.embedding_text)

		item = TicketKnowledgeItem.create(
			id=uuid4(), source_id=command.ticket_id, application=command.application,
			embedding=embedding, embedding_model=self.embedding_provider.model_name,
			embedding_model_version=self.embedding_provider.model_version,
			generated_at=command.created_at, identifiers=list(preprocessed.identifiers),
			genergy_id=command.genergy_id, oceane_id=command.oceane_id,
		)
		# Durable immediately, unlike the session-staged write this replaced -- so unlike before, the
		# new ticket is already a searchable candidate by the time the searches below run. It never
		# shows up in its own results only because both searches exclude it explicitly, which they
		# always did.
		await self.knowledge_items.add(item)

		# Searched from the item just built rather than from the loose embedding and identifiers it
		# was built out of, so this path and the two that recompute results from stored vectors are
		# demonstrably the same computation and not merely written to look alike.
		results = await self.computation.results_for(item, command.created_at)
		await self.uow.similarity_results.replace_for_source(command.ticket_id, results)

		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise

		await self.event_publisher.publish(
			SimilarityResultsGenerated(
				ticket_id=command.ticket_id, result_count=len(results), occurred_at=command.created_at,
			)
		)
