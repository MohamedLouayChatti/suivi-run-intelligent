from __future__ import annotations

from app.modules.knowledge_base.application.dto.recalculation_schedule_dto import RecalculationScheduleDTO
from app.modules.knowledge_base.application.interfaces.recalculation_runner import RecalculationRunner
from app.modules.knowledge_base.application.queries.get_recalculation_schedule.query import (
	GetRecalculationScheduleQuery,
)
from app.modules.knowledge_base.application.support.recalculation_job import SIMILARITY_RECALCULATION_JOB_NAME
from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.modules.knowledge_base.domain.repositories.similarity_recalculation_schedule_repository import (
	SimilarityRecalculationScheduleRepository,
)
from app.workers.jobs import JobScheduler


class GetRecalculationScheduleHandler:
	"""Answers what the schedule is, when it will next fire, and whether it is firing right now.

	Takes the domain repository rather than a dedicated read repository, which is the one place
	this module departs from the read/write split elsewhere. The reason is that there is nothing to
	project: the read is a single row whose every field is already the shape the response wants, so
	a second repository returning a second shape of the same five values would be ceremony rather
	than separation. It still behaves like a read handler in every way that matters -- its own
	session, no unit of work, no transaction, a DTO out.

	The other two sources are read from the running process and cost nothing: the scheduler's own
	next firing, and the runner's in-flight flag.
	"""

	def __init__(
		self,
		schedules: SimilarityRecalculationScheduleRepository,
		scheduler: JobScheduler,
		runner: RecalculationRunner,
	) -> None:
		self.schedules = schedules
		self.scheduler = scheduler
		self.runner = runner

	async def handle(self, query: GetRecalculationScheduleQuery) -> RecalculationScheduleDTO:
		# No row means nobody has configured one, which is not a gap: the code default is in force
		# and is what the scheduler was registered with at startup.
		schedule = await self.schedules.get() or SimilarityRecalculationSchedule.default()
		return RecalculationScheduleDTO.from_schedule(
			schedule,
			next_run_at=self.scheduler.next_run_at(SIMILARITY_RECALCULATION_JOB_NAME),
			running=self.runner.is_running,
		)
