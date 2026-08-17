from __future__ import annotations

import logging

from app.modules.knowledge_base.application.commands.generate_similarity_results.command import (
	GenerateSimilarityResultsCommand,
)
from app.modules.knowledge_base.application.commands.generate_similarity_results.handler import (
	GenerateSimilarityResultsHandler,
)
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

	Dependencies split by lifetime, not by layer. The Postgres session is built fresh per call --
	this handler instance is subscribed once and reused across concurrent requests, so a session
	held on it would be shared mutable state, the same reason AuditEventHandler builds its UoW per
	call. The vector-store collaborators go the other way: both are stateless wrappers over one
	pooled client, so they are built once at subscription time and reused, exactly like the
	embedding provider next to them.
	"""

	def __init__(
		self,
		knowledge_items: QdrantKnowledgeItemRepository,
		search_port: QdrantSimilaritySearch,
		embedding_provider: EmbeddingProvider,
		event_publisher: EventPublisher,
	) -> None:
		self.knowledge_items = knowledge_items
		self.search_port = search_port
		self.embedding_provider = embedding_provider
		self.event_publisher = event_publisher

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
				search_port=self.search_port,
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
