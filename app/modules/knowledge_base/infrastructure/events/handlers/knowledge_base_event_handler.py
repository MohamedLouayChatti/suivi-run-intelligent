from __future__ import annotations

import logging

from app.modules.knowledge_base.application.commands.generate_similarity_results.command import (
	GenerateSimilarityResultsCommand,
)
from app.modules.knowledge_base.application.commands.generate_similarity_results.handler import (
	GenerateSimilarityResultsHandler,
)
from app.modules.knowledge_base.infrastructure.persistence.repositories.pgvector_similarity_search import (
	PgvectorSimilaritySearch,
)
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.shared.ai.embedding_provider import EmbeddingProvider
from app.shared.database.session import create_session
from app.shared.events.event import DomainEvent
from app.shared.events.event_publisher import EventPublisher
from app.shared.events.handler import EventHandler

logger = logging.getLogger(__name__)


class KnowledgeBaseEventHandler(EventHandler):
	"""Subscribed to TicketCreated only. Builds one fresh
	session per call, shared by the UoW (writes) and the search port (a read that happens
	mid-write, deliberately kept off the UoW interface itself, the same way
	AuditEventHandler builds a fresh UoW per call: this handler instance is subscribed once and
	reused across concurrent requests, so nothing here can be shared state.
	"""

	def __init__(self, embedding_provider: EmbeddingProvider, event_publisher: EventPublisher) -> None:
		self.embedding_provider = embedding_provider
		self.event_publisher = event_publisher

	async def handle(self, event: DomainEvent) -> None:
		if not isinstance(event, TicketCreated):
			logger.warning("KnowledgeBaseEventHandler received unexpected event type %s", type(event).__name__)
			return

		session = create_session()
		try:
			uow = SqlAlchemyUnitOfWork(session)
			search_port = PgvectorSimilaritySearch(session)
			handler = GenerateSimilarityResultsHandler(uow, self.embedding_provider, search_port, self.event_publisher)
			command = GenerateSimilarityResultsCommand(
				ticket_id=event.ticket_id, description=event.description,
				application=event.application, created_at=event.occurred_at,
			)
			await handler.handle(command)
		finally:
			await session.close()
