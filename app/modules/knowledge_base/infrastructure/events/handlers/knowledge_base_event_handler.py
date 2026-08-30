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

	One ticket creation changes the graph in two directions -- the new ticket gets results of its
	own, and the older tickets it matched need refreshing so they point back at it -- and *neither*
	is done in the request that created the ticket. Both run in a single background job.

	Generation used to be awaited here, on the reasoning that a reader opening the ticket should
	find its results already there. What that actually bought was small and what it cost was not.
	The event bus dispatches handlers inline, so a ticket creation was transitively blocking on a
	remote embedding call: on this deployment that means loading a 1.2 GB model on a CPU-only
	machine, which under Ollama's default residency window nearly every ticket paid in full. Worse,
	the failure path was the expensive one -- an unreachable Ollama spent three connection timeouts
	and three seconds of backoff inside the request before the bus logged the error and creation
	succeeded anyway. The person waiting was the one who wrote the description, and they are not the
	reader the results were being rushed for; that reader opens the ticket later, by which time the
	job has long finished.

	So the deferral boundary moved rather than the work: everything this module does about a new
	ticket is now background work, and ticket creation is independent of whether Ollama is fast,
	slow or down. It is also what the module boundary already asked for -- Ticket Management
	integrates with this module through a domain event precisely so it does not wait on it.

	Both halves qualify for InProcessJobRunner on the same three counts: they need nothing from the
	request (no CurrentUser, no session, no in-memory state -- just a ticket id and the event's own
	fields), they are idempotent, and losing one costs staleness the rebuild pass repairs rather
	than anything unrecoverable.

	They are one job rather than two because the second depends on the first: the refresh reads back
	the results generation committed, and two separately enqueued jobs are independent asyncio tasks
	with no ordering between them. Awaiting them in sequence inside one job is what keeps "refresh
	only what generation actually produced" true, and lets a failed generation skip the refresh by
	simply propagating -- run_job logs it and stops there.

	What the reader now sees while the job is in flight is not "no similar incidents" but an
	explicit pending state: GetSimilarIncidentsHandler distinguishes the two by asking the corpus
	whether this ticket has been embedded yet.

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

		# The whole of this handler's work, off the request and onto the runner. Nothing is awaited
		# here beyond the enqueue itself, so what ticket creation now pays this module is one
		# put onto an in-memory queue.
		await self.job_queue.enqueue(
			self._index_ticket_job(event),
			name=f"knowledge_base.index_ticket[{event.ticket_id}]",
		)

	def _index_ticket_job(self, event: TicketCreated) -> Job:
		"""Builds the deferred work as a closure over the event, to run whenever the runner gets to
		it.

		Closing over the event and nothing else is what makes it safe to run arbitrarily later:
		every other thing it needs is either carried on the event or already durable somewhere it
		reads at run time. In particular it opens its own sessions when it runs rather than being
		handed one from here -- the job outlives this call, so anything it borrowed would be closed
		underneath it.

		No try/except of its own: `run_job` is the shared safety net that logs a failed job and
		stops it there. What a failure means is unchanged by being deferred -- the ticket exists
		either way, the corpus and the graph keep whatever they already had, and the rebuild pass
		reconciles them.
		"""

		async def index_ticket() -> None:
			await self._generate_results(event)
			# Reached only when generation committed. If it raised, there are no results whose
			# neighbours could need refreshing, and the exception is already on its way to run_job.
			await self._refresh_neighbors(event)

		return index_ticket

	async def _generate_results(self, event: TicketCreated) -> None:
		"""Embeds the new ticket, writes it to the corpus and gives it results of its own."""
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

	async def _refresh_neighbors(self, event: TicketCreated) -> None:
		"""Lets the older tickets the new one matched point back at it.

		Roughly 14 of the pipeline's 16 vector searches, and the reason this half was already
		deferred before generation joined it. Everything it needs is either already committed (the
		neighbour list, read back from the graph) or already durable in the corpus (their vectors).
		"""
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
