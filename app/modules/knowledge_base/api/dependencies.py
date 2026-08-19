from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.modules.knowledge_base.application.commands.import_ticket_batch.handler import ImportTicketBatchHandler
from app.modules.knowledge_base.application.commands.trigger_similarity_recalculation.handler import (
	TriggerSimilarityRecalculationHandler,
)
from app.modules.knowledge_base.application.commands.update_recalculation_schedule.handler import (
	UpdateRecalculationScheduleHandler,
)
from app.modules.knowledge_base.application.queries.get_recalculation_schedule.handler import (
	GetRecalculationScheduleHandler,
)
from app.modules.knowledge_base.application.queries.get_similar_incidents.handler import GetSimilarIncidentsHandler
from app.modules.knowledge_base.application.services.corpus_ingestion import CorpusIngestion
from app.modules.knowledge_base.infrastructure.jobs.similarity_recalculation_runner import (
	similarity_recalculation_runner,
)
from app.modules.knowledge_base.infrastructure.persistence.repositories.sqlalchemy_similarity_read_repository import (
	SqlAlchemySimilarityReadRepository,
)
from app.modules.knowledge_base.infrastructure.persistence.repositories.sqlalchemy_similarity_recalculation_schedule_repository import (
	SqlAlchemySimilarityRecalculationScheduleRepository,
)
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.knowledge_base.infrastructure.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from app.modules.knowledge_base.infrastructure.vector_store.client import get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.auth.api.dependencies import get_user_read_repository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.ticket_management.api.dependencies import (
	get_event_publisher as get_ticket_event_publisher,
	get_read_repository as get_ticket_read_repository,
	get_unit_of_work as get_ticket_unit_of_work,
)
from app.modules.ticket_management.application.commands.discard_imported_tickets.handler import (
	DiscardImportedTicketsHandler,
)
from app.modules.ticket_management.application.commands.import_tickets.handler import ImportTicketsHandler
from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import (
	SqlAlchemyUnitOfWork as TicketUnitOfWork,
)
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)
from app.shared.database.session import create_session
from app.workers.worker import job_queue, job_scheduler


async def get_similarity_read_repository() -> AsyncIterator[SqlAlchemySimilarityReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemySimilarityReadRepository(session)
	finally:
		await session.close()


def get_get_similar_incidents_handler(
	similarity_read_repository: Annotated[SqlAlchemySimilarityReadRepository, Depends(get_similarity_read_repository)],
	ticket_read_repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_ticket_read_repository)],
) -> GetSimilarIncidentsHandler:
	return GetSimilarIncidentsHandler(similarity_read_repository, ticket_read_repository)


async def get_recalculation_schedule_repository() -> AsyncIterator[
	SqlAlchemySimilarityRecalculationScheduleRepository
]:
	session = create_session()
	try:
		yield SqlAlchemySimilarityRecalculationScheduleRepository(session)
	finally:
		await session.close()


def get_get_recalculation_schedule_handler(
	schedules: Annotated[
		SqlAlchemySimilarityRecalculationScheduleRepository, Depends(get_recalculation_schedule_repository)
	],
) -> GetRecalculationScheduleHandler:
	# The scheduler and the runner are the process-wide singletons, not per-request objects: what
	# this read reports is the state of the one clock and the one pass, so a fresh instance of
	# either would have nothing to say.
	return GetRecalculationScheduleHandler(schedules, job_scheduler, similarity_recalculation_runner)


def get_update_recalculation_schedule_handler() -> UpdateRecalculationScheduleHandler:
	return UpdateRecalculationScheduleHandler(
		SqlAlchemyUnitOfWork(), job_scheduler, similarity_recalculation_runner
	)


def get_trigger_similarity_recalculation_handler() -> TriggerSimilarityRecalculationHandler:
	return TriggerSimilarityRecalculationHandler(similarity_recalculation_runner, job_queue)


def get_import_ticket_batch_handler(
	ticket_uow: Annotated[TicketUnitOfWork, Depends(get_ticket_unit_of_work)],
	ticket_event_publisher: Annotated[InMemoryEventPublisher, Depends(get_ticket_event_publisher)],
	ticket_read_repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_ticket_read_repository)],
	users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)],
) -> ImportTicketBatchHandler:
	"""Composes the one operation in this codebase that drives two modules' writes.

	Ticket Management's own dependencies are resolved through Ticket Management's dependency
	providers rather than rebuilt here, so its unit of work, its event publisher and its read
	repository are constructed and torn down exactly as they are for its own routes -- this module
	composes that module's application handlers, it does not reimplement how they are wired.

	The compensating handler is given a unit of work of its own, deliberately: it runs after the
	import has committed and closed, so a shared one would already be finished by the time it is
	needed.

	The Qdrant collaborators and the embedding provider are built per request, as they are
	everywhere else in this module: both are stateless wrappers over the pooled client, and
	constructing them does no I/O. The runner and the queue are the process-wide singletons, since
	a fresh runner would carry a second in-flight flag that knows nothing about the real one.
	"""
	return ImportTicketBatchHandler(
		import_tickets=ImportTicketsHandler(
			uow=ticket_uow,
			event_publisher=ticket_event_publisher,
			ticket_read_repository=ticket_read_repository,
			users=users,
		),
		discard_imported_tickets=DiscardImportedTicketsHandler(TicketUnitOfWork(), ticket_event_publisher),
		knowledge_items=QdrantKnowledgeItemRepository(get_qdrant_client()),
		ingestion=CorpusIngestion(OllamaEmbeddingProvider.from_settings()),
		runner=similarity_recalculation_runner,
		job_queue=job_queue,
	)
