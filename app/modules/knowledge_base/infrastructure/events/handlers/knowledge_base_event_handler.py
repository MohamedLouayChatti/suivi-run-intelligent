from __future__ import annotations

import logging

from app.modules.knowledge_base.application.commands.generate_similarity_results.command import (
	GenerateSimilarityResultsCommand,
)
from app.modules.knowledge_base.application.commands.generate_similarity_results.handler import (
	GenerateSimilarityResultsHandler,
)
from app.modules.knowledge_base.application.commands.refresh_neighbor_similarity.command import (
	RefreshNeighborSimilarityCommand,
)
from app.modules.knowledge_base.application.commands.refresh_neighbor_similarity.handler import (
	RefreshNeighborSimilarityHandler,
)
from app.modules.knowledge_base.application.services.similarity_computation import SimilarityComputation
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_similarity_search import QdrantSimilaritySearch
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.shared.ai.embedding_provider import EmbeddingProvider
from app.shared.database.session import create_session
from app.shared.events.event import DomainEvent
from app.shared.events.event_publisher import EventPublisher
from app.shared.events.handler import EventHandler
from app.workers.jobs import Job, JobQueue

logger = logging.getLogger(__name__)


class KnowledgeBaseEventHandler(EventHandler):
	"""Subscribed to TicketCreated only.

	One ticket creation changes the graph in two directions, and the two are split here by whether
	anyone is waiting for them. Generation -- which gives the new ticket its own results -- is
	awaited, so those results are already durable by the time the creation response returns and a
	reader opening the ticket finds them. The one-hop refresh, which lets the older tickets it
	matched point back at it, is enqueued as a background job instead: it is roughly 14 of the
	pipeline's 16 vector searches and nothing in that request reads what it writes, so paying for it
	inline would be charging the person creating a ticket for maintenance on rows they will never
	look at.

	Only what is genuinely deferrable is deferred. The refresh qualifies on three counts: it needs
	nothing from the request (no CurrentUser, no session, no in-memory state -- just a ticket id it
	reads committed state from), it is idempotent, and losing it costs staleness that the rebuild
	pass repairs rather than anything unrecoverable. That is exactly the contract InProcessJobRunner
	asks for, and the reason this is the first job in the codebase rather than an arbitrary one.

	Dependencies split by lifetime, not by layer. Postgres sessions are built fresh per use -- this
	handler instance is subscribed once and reused across concurrent requests, so a session held on
	it would be shared mutable state, the same reason AuditEventHandler builds its UoW per call. The
	vector-store collaborators go the other way: both are stateless wrappers over one pooled client,
	so they are built once at subscription time and reused, exactly like the embedding provider next
	to them -- and the computation service wrapping the search port is stateless for the same
	reason, so it is built once here too.
	"""

	def __init__(
		self,
		knowledge_items: QdrantKnowledgeItemRepository,
		search_port: QdrantSimilaritySearch,
		embedding_provider: EmbeddingProvider,
		event_publisher: EventPublisher,
		job_queue: JobQueue,
	) -> None:
		self.knowledge_items = knowledge_items
		self.embedding_provider = embedding_provider
		self.event_publisher = event_publisher
		self.job_queue = job_queue
		self.computation = SimilarityComputation(search_port)

	async def handle(self, event: DomainEvent) -> None:
		if not isinstance(event, TicketCreated):
			logger.warning("KnowledgeBaseEventHandler received unexpected event type %s", type(event).__name__)
			return

		session = create_session()
		try:
			handler = GenerateSimilarityResultsHandler(
				uow=SqlAlchemyUnitOfWork(session),
				knowledge_items=self.knowledge_items,
				embedding_provider=self.embedding_provider,
				computation=self.computation,
				event_publisher=self.event_publisher,
			)
			command = GenerateSimilarityResultsCommand(
				ticket_id=event.ticket_id, description=event.description,
				application=event.application, created_at=event.occurred_at,
				genergy_id=event.genergy_id, oceane_id=event.oceane_id,
			)
			await handler.handle(command)
		finally:
			await session.close()

		# Reached only when generation committed: if it raised, there are no results whose
		# neighbours could need refreshing, and the exception is already on its way to the event bus.
		# Enqueued after the session above is closed, and never handed that session -- the job
		# outlives this call, so anything it borrowed from here would be closed underneath it.
		await self.job_queue.enqueue(
			self._refresh_neighbors_job(event),
			name=f"knowledge_base.refresh_neighbors[{event.ticket_id}]",
		)

	def _refresh_neighbors_job(self, event: TicketCreated) -> Job:
		"""Builds the deferred half as a closure over the event, to run whenever the runner gets to
		it.

		It opens its own session, at run time rather than at enqueue time, for the reason above.
		Everything else it needs is either already committed (the neighbour list, read back from the
		graph) or already durable in the corpus (their vectors), which is why a job that may run
		well after the request that scheduled it still computes the right thing.

		No try/except of its own: `run_job` is the shared safety net that logs a failed job and
		stops it there. What a failure means here is unchanged by being deferred -- the new ticket's
		own results stand, the neighbours keep the results they already had, and the rebuild pass
		reconciles them.
		"""

		async def refresh_neighbors() -> None:
			session = create_session()
			try:
				handler = RefreshNeighborSimilarityHandler(
					uow=SqlAlchemyUnitOfWork(session),
					knowledge_items=self.knowledge_items,
					computation=self.computation,
				)
				refreshed = await handler.handle(
					RefreshNeighborSimilarityCommand(
						source_ticket_id=event.ticket_id, generated_at=event.occurred_at,
					)
				)
				logger.info(
					"Refreshed similarity results for %d neighbour(s) of ticket %s", refreshed, event.ticket_id
				)
			finally:
				await session.close()

		return refresh_neighbors
