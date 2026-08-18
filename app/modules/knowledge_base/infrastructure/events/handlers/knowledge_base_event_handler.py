from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

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

logger = logging.getLogger(__name__)


class KnowledgeBaseEventHandler(EventHandler):
	"""Subscribed to TicketCreated only.

	Runs two application handlers in order, because one ticket creation changes the graph in two
	directions and only the first of them is the new ticket's own business: generation gives the new
	ticket its results, then the bounded one-hop refresh gives the older tickets it matched a chance
	to point back at it. Sequencing them here rather than nesting one inside the other is what keeps
	each handler a single unit of work with its own transaction and its own failure meaning.

	Dependencies split by lifetime, not by layer. The Postgres session is built fresh per call --
	this handler instance is subscribed once and reused across concurrent requests, so a session
	held on it would be shared mutable state, the same reason AuditEventHandler builds its UoW per
	call. The vector-store collaborators go the other way: both are stateless wrappers over one
	pooled client, so they are built once at subscription time and reused, exactly like the
	embedding provider next to them -- and the computation service wrapping the search port is
	stateless for the same reason, so it is built once here too.
	"""

	def __init__(
		self,
		knowledge_items: QdrantKnowledgeItemRepository,
		search_port: QdrantSimilaritySearch,
		embedding_provider: EmbeddingProvider,
		event_publisher: EventPublisher,
	) -> None:
		self.knowledge_items = knowledge_items
		self.embedding_provider = embedding_provider
		self.event_publisher = event_publisher
		self.computation = SimilarityComputation(search_port)

	async def handle(self, event: DomainEvent) -> None:
		if not isinstance(event, TicketCreated):
			logger.warning("KnowledgeBaseEventHandler received unexpected event type %s", type(event).__name__)
			return

		# One session, two transactions. The generation commits before the refresh opens its own, so
		# the new ticket's results are already durable and cannot be undone by anything the refresh
		# does; sharing the session only shares the connection, never the transaction.
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

			# Only reached when generation succeeded: if it raised, there are no results to refresh
			# the neighbours of, and the exception is already on its way to the event bus.
			await self._refresh_neighbors(session, event)
		finally:
			await session.close()

	async def _refresh_neighbors(self, session: AsyncSession, event: TicketCreated) -> None:
		"""Best effort, and the decision that it is best effort lives here rather than in the
		handler.

		The handler raises like any other, so an admin or CLI trigger for it later would learn that
		it failed. In *this* path the failure is worth a log line and nothing more: the new ticket's
		own results are already committed, a failed refresh leaves the neighbours exactly as stale as
		they were a moment ago rather than corrupt, and the rebuild pass repairs that by design.
		Letting it escape would only reach InMemoryEventBus, which logs handler failures and carries
		on regardless -- so the choice is not whether ticket creation survives but whether a
		recoverable staleness is reported as an error with a traceback.
		"""
		handler = RefreshNeighborSimilarityHandler(
			uow=SqlAlchemyUnitOfWork(session),
			knowledge_items=self.knowledge_items,
			computation=self.computation,
		)
		try:
			refreshed = await handler.handle(
				RefreshNeighborSimilarityCommand(
					source_ticket_id=event.ticket_id, generated_at=event.occurred_at,
				)
			)
		except Exception:
			logger.warning(
				"Neighbor similarity refresh failed for ticket %s; its own results stand and the "
				"neighbours keep their previous ones until the next rebuild.",
				event.ticket_id, exc_info=True,
			)
			return

		logger.info("Refreshed similarity results for %d neighbour(s) of ticket %s", refreshed, event.ticket_id)
