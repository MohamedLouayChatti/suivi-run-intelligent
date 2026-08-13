from __future__ import annotations

from uuid import uuid4

from app.modules.knowledge_base.application.commands.generate_similarity_results.command import (
	GenerateSimilarityResultsCommand,
)
from app.modules.knowledge_base.application.interfaces.similarity_search_port import SimilaritySearchPort
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.domain.entities.knowledge_item import TicketKnowledgeItem
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.events.similarity_results_generated import SimilarityResultsGenerated
from app.modules.knowledge_base.domain.services.description_preprocessor import preprocess_description
from app.modules.knowledge_base.domain.services.similarity_ranking import (
	ALGORITHM_VERSION,
	MAX_RESULTS,
	MIN_SIMILARITY_THRESHOLD,
	rank_candidates,
)
from app.shared.ai.embedding_provider import EmbeddingProvider
from app.shared.events.event_publisher import EventPublisher


class GenerateSimilarityResultsHandler:
	"""Reacts to TicketCreated (via the infrastructure event handler): preprocess -> embed ->
	semantic + reference search -> rank -> persist -> publish. Bounded incremental neighbor
	refresh is a separate, not-yet-built follow-up -- this handler only ever generates results
	for the one ticket it was triggered for.

	Ingestion and query preprocessing cannot drift here: this handler ingests the new ticket and
	queries with it in the same call, from the same single `preprocess_description` result.
	"""

	def __init__(
		self, uow: UnitOfWork, embedding_provider: EmbeddingProvider,
		search_port: SimilaritySearchPort, event_publisher: EventPublisher,
	) -> None:
		self.uow = uow
		self.embedding_provider = embedding_provider
		self.search_port = search_port
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
		await self.uow.knowledge_items.add(item)

		semantic = await self.search_port.find_nearest(
			embedding, application=command.application, exclude_ticket_id=command.ticket_id, limit=MAX_RESULTS,
		)
		referenced = await self.search_port.find_referenced(
			embedding, preprocessed.identifiers,
			application=command.application, exclude_ticket_id=command.ticket_id,
		)
		ranked = rank_candidates(
			semantic=semantic, referenced=referenced,
			min_similarity_score=MIN_SIMILARITY_THRESHOLD, max_results=MAX_RESULTS,
		)

		results = [
			SimilarityResult.create(
				id=uuid4(), source_ticket_id=command.ticket_id, similar_ticket_id=candidate.ticket_id,
				similarity_score=candidate.similarity_score, rank=candidate.rank,
				generated_at=command.created_at,
				embedding_model_version=self.embedding_provider.model_version,
				algorithm_version=ALGORITHM_VERSION,
			)
			for candidate in ranked
		]
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
