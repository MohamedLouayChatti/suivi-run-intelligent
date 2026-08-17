from __future__ import annotations

from app.modules.knowledge_base.infrastructure.events.handlers.knowledge_base_event_handler import (
	KnowledgeBaseEventHandler,
)
from app.modules.knowledge_base.infrastructure.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from app.modules.knowledge_base.infrastructure.vector_store.client import get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_similarity_search import QdrantSimilaritySearch
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


def register_subscriptions(registry: SubscriptionRegistry, event_bus: InMemoryEventBus) -> None:
	"""Subscribes to TicketCreated only.

	Takes `event_bus` (unlike every other module's register_subscriptions, which only takes
	`registry`) because this is the first handler that needs to publish an event of its own
	(SimilarityResultsGenerated) rather than just consume -- it needs an EventPublisher built at
	subscription time, and the bus is what that publisher wraps. No shared interface enforces a
	fixed signature across modules' bootstrap.py files, so this is a self-contained addition.
	"""
	# One instance of each for the process, not one per event. The embedding provider caches the
	# resolved model build behind an asyncio.Lock, so sharing it means one resolution round trip in
	# total rather than one per ticket created; the two vector-store collaborators share a single
	# pooled Qdrant client for the same reason.
	#
	# None of this does I/O. An unreachable Ollama or Qdrant therefore cannot stop the application
	# from starting -- it surfaces on the first ticket instead, where InMemoryEventBus logs it and
	# lets the rest of ticket creation succeed. A *missing* QDRANT_CLUSTER_ENDPOINT does stop it,
	# and should: that is a configuration error with no working degraded mode, and it is better
	# named at boot than rediscovered once per ticket. The collection itself is provisioned by an
	# explicit CLI pass, never from here.
	qdrant = get_qdrant_client()
	handler = KnowledgeBaseEventHandler(
		knowledge_items=QdrantKnowledgeItemRepository(qdrant),
		search_port=QdrantSimilaritySearch(qdrant),
		embedding_provider=OllamaEmbeddingProvider.from_settings(),
		event_publisher=InMemoryEventPublisher(event_bus),
	)
	registry.subscribe(TicketCreated, handler)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Knowledge Base registers no policy of its own -- its read endpoint reuses Ticket
	Management's already-registered "ticket" policy via require_instance_permission."""
	return None
