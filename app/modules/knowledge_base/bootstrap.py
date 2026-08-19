from __future__ import annotations

from app.modules.knowledge_base.application.support.recalculation_job import (
	SIMILARITY_RECALCULATION_JOB_NAME,
	to_weekly_schedule,
)
from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.modules.knowledge_base.infrastructure.events.handlers.knowledge_base_event_handler import (
	KnowledgeBaseEventHandler,
)
from app.modules.knowledge_base.infrastructure.jobs.similarity_recalculation_runner import (
	similarity_recalculation_runner,
)
from app.modules.knowledge_base.infrastructure.persistence.repositories.sqlalchemy_similarity_recalculation_schedule_repository import (
	SqlAlchemySimilarityRecalculationScheduleRepository,
)
from app.modules.knowledge_base.infrastructure.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from app.modules.knowledge_base.infrastructure.vector_store.client import get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_similarity_search import QdrantSimilaritySearch
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.shared.database.session import create_session
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry
from app.workers.jobs import JobScheduler
from app.workers.worker import job_queue


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
		# The process-wide runner, injected rather than imported inside the handler so a test or a
		# future worker process can supply a different JobQueue without touching the module.
		job_queue=job_queue,
	)
	registry.subscribe(TicketCreated, handler)


async def register_scheduled_jobs(scheduler: JobScheduler) -> None:
	"""Registers the full similarity graph recalculation on the configured schedule.

	The one hook in this module that reads the database at startup, and the only way the persisted
	schedule can reach an in-memory scheduler: there is no job store, deliberately, so the table is
	the single source of truth about when the pass runs and every start re-registers from it.

	A failure here stops the application from starting rather than being caught and replaced with
	the defaults. Postgres is a hard dependency of every request this application serves, so a
	failed read of one row at boot is a genuine boot failure -- and quietly falling back would run
	the pass on a schedule nobody chose, including on an installation where an administrator had
	turned it off.

	What it registers is the runner, not a recalculation composed here: `run` is the same bound
	method the manual trigger enqueues, which is what makes "scheduled" and "run now" two doors
	into one operation rather than two operations that resemble each other.
	"""
	session = create_session()
	try:
		repository = SqlAlchemySimilarityRecalculationScheduleRepository(session)
		schedule = await repository.get() or SimilarityRecalculationSchedule.default()
	finally:
		await session.close()

	await scheduler.register(
		similarity_recalculation_runner.run,
		name=SIMILARITY_RECALCULATION_JOB_NAME,
		schedule=to_weekly_schedule(schedule),
		enabled=schedule.enabled,
	)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Knowledge Base registers no policy of its own -- its read endpoint reuses Ticket
	Management's already-registered "ticket" policy via require_instance_permission.

	The recalculation endpoints register nothing either, and could not: they configure and start a
	pass over the whole corpus, so there is no instance to authorize against. They are gated by
	their own permissions alone.
	"""
	return None
