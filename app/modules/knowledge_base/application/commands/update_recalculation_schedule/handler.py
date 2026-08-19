from __future__ import annotations

import logging

from app.modules.knowledge_base.application.commands.update_recalculation_schedule.command import (
	UpdateRecalculationScheduleCommand,
)
from app.modules.knowledge_base.application.dto.recalculation_schedule_dto import RecalculationScheduleDTO
from app.modules.knowledge_base.application.interfaces.recalculation_runner import RecalculationRunner
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.application.support.recalculation_job import (
	SIMILARITY_RECALCULATION_JOB_NAME,
	to_weekly_schedule,
)
from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.modules.knowledge_base.domain.events.similarity_recalculation_schedule_updated import (
	SimilarityRecalculationScheduleUpdated,
)
from app.shared.events.event_publisher import EventPublisher
from app.workers.jobs import JobScheduler

logger = logging.getLogger(__name__)


class UpdateRecalculationScheduleHandler:
	"""Persists a new schedule, then points the running scheduler at it.

	The order is the one this codebase uses everywhere a commit is followed by an effect the
	outside world can see: persist, commit, then act. A reschedule applied before the commit would
	survive a rollback, leaving a process firing on a schedule no row records -- and a restart
	would silently undo it, which is the worst kind of configuration bug because it fixes itself
	just often enough not to be reported.

	Applying the change immediately is why the schedule is in a table at all. Nothing here restarts
	or reloads: the scheduler is handed the new trigger and the next firing moves.

	A pass already in flight is not interrupted. The schedule says when runs start, not how long
	one may take, and cancelling a partly-finished rebuild would leave the graph half rebuilt for
	no benefit -- the running pass finishes, and the next one starts at the new time.
	"""

	def __init__(
		self,
		uow: UnitOfWork,
		scheduler: JobScheduler,
		runner: RecalculationRunner,
		event_publisher: EventPublisher,
	) -> None:
		self.uow = uow
		self.scheduler = scheduler
		self.runner = runner
		self.event_publisher = event_publisher

	async def handle(self, command: UpdateRecalculationScheduleCommand) -> RecalculationScheduleDTO:
		# Built through the domain factory, so an impossible time or an unknown timezone is refused
		# before it reaches either store or scheduler -- the API schema checks the same ranges, but
		# it is not the only possible caller and must not be the only guard.
		schedule = SimilarityRecalculationSchedule.create(
			enabled=command.enabled, days_of_week=command.days_of_week, hour=command.hour,
			minute=command.minute, timezone=command.timezone, updated_at=command.updated_at,
			updated_by=command.actor_id,
		)

		async with self.uow as uow:
			await uow.recalculation_schedule.save(schedule)
			await uow.commit()

		# Published between the commit and the reschedule, and that placement is the deliberate
		# half of it. The row is what this codebase treats as the truth about when the pass runs --
		# every startup re-registers the scheduler from it -- so the fact worth announcing is that
		# the row changed, and it has. Publishing after the reschedule instead would let a
		# scheduler failure erase the audit record of a change that survived it, which is the worse
		# of the two ways this can be wrong.
		await self.event_publisher.publish(
			SimilarityRecalculationScheduleUpdated(
				enabled=schedule.enabled,
				days_of_week=schedule.days_in_week_order(),
				hour=schedule.hour,
				minute=schedule.minute,
				timezone=schedule.timezone,
				occurred_at=command.updated_at,
				actor_id=command.actor_id,
			)
		)

		await self.scheduler.reschedule(
			SIMILARITY_RECALCULATION_JOB_NAME,
			schedule=to_weekly_schedule(schedule),
			enabled=schedule.enabled,
		)
		logger.info(
			"Similarity recalculation schedule updated by %s: enabled=%s, days=%s, %02d:%02d %s.",
			command.actor_id, schedule.enabled,
			",".join(day.value for day in schedule.days_in_week_order()),
			schedule.hour, schedule.minute, schedule.timezone,
		)

		return RecalculationScheduleDTO.from_schedule(
			schedule,
			next_run_at=self.scheduler.next_run_at(SIMILARITY_RECALCULATION_JOB_NAME),
			running=self.runner.is_running,
		)
