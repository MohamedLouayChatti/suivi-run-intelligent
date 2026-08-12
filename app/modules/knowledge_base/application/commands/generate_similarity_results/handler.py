from __future__ import annotations

from uuid import uuid4

from app.modules.knowledge_base.application.commands.generate_similarity_results.command import (
	GenerateSimilarityResultsCommand,
)
from app.modules.knowledge_base.application.interfaces.similarity_search_port import SimilaritySearchPort
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.enums.knowledge_source_type import KnowledgeSourceType
from app.modules.knowledge_base.domain.events.similarity_results_generated import SimilarityResultsGenerated
from app.shared.ai.embedding_provider import EmbeddingProvider
from app.shared.events.event_publisher import EventPublisher

# Placeholders, not yet evaluated against real data.
MIN_SIMILARITY_THRESHOLD = 0.6
MAX_RESULTS = 7
ALGORITHM_VERSION = "v1"


class GenerateSimilarityResultsHandler:
	"""Reacts to TicketCreated (via the infrastructure event handler): embed -> search ->
	threshold/cap -> persist -> publish. Bounded incremental neighbor refresh is
	a separate, not-yet-built follow-up -- this handler only ever generates results for the one
	ticket it was triggered for.
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
		embedding = await self.embedding_provider.embed(command.description)

		item = KnowledgeItem.create(
			id=uuid4(), source_type=KnowledgeSourceType.TICKET, source_id=command.ticket_id,
			application=command.application, embedding=embedding,
			embedding_model=self.embedding_provider.model_name,
			embedding_model_version=self.embedding_provider.model_version,
			generated_at=command.created_at,
		)
		await self.uow.knowledge_items.add(item)

		candidates = await self.search_port.find_nearest(
			embedding, application=command.application, exclude_ticket_id=command.ticket_id, limit=MAX_RESULTS,
		)
		results = [
			SimilarityResult.create(
				id=uuid4(), source_ticket_id=command.ticket_id, similar_ticket_id=candidate.ticket_id,
				similarity_score=candidate.similarity_score, rank=rank, generated_at=command.created_at,
				embedding_model_version=self.embedding_provider.model_version, algorithm_version=ALGORITHM_VERSION,
			)
			for rank, candidate in enumerate(candidates, start=1)
			if candidate.similarity_score >= MIN_SIMILARITY_THRESHOLD
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
