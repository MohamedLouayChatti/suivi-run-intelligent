from __future__ import annotations

from app.modules.knowledge_base.infrastructure.events.handlers.knowledge_base_event_handler import (
	KnowledgeBaseEventHandler,
)
from app.modules.knowledge_base.infrastructure.providers.ollama_embedding_provider import OllamaEmbeddingProvider
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
	# One provider instance for the process, not one per event: it caches the resolved model build
	# behind an asyncio.Lock, so sharing it means one resolution round trip in total rather than one
	# per ticket created. Construction does no I/O, so an unreachable Ollama cannot stop the app
	# from starting -- it surfaces on the first ticket instead, where InMemoryEventBus logs it and
	# lets the rest of ticket creation succeed.
	handler = KnowledgeBaseEventHandler(
		embedding_provider=OllamaEmbeddingProvider.from_settings(),
		event_publisher=InMemoryEventPublisher(event_bus),
	)
	registry.subscribe(TicketCreated, handler)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Knowledge Base registers no policy of its own -- its read endpoint reuses Ticket
	Management's already-registered "ticket" policy via require_instance_permission."""
	return None
