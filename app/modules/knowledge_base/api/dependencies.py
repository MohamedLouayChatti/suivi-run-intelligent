from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

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
from app.modules.ticket_management.api.dependencies import get_read_repository as get_ticket_read_repository
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
