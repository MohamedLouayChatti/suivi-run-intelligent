from __future__ import annotations

import logging
from functools import partial

from app.modules.knowledge_base.application.commands.trigger_similarity_recalculation.command import (
	TriggerSimilarityRecalculationCommand,
)
from app.modules.knowledge_base.application.exceptions import RecalculationAlreadyRunning
from app.modules.knowledge_base.application.interfaces.recalculation_runner import RecalculationRunner
from app.modules.knowledge_base.application.support.recalculation_job import SIMILARITY_RECALCULATION_JOB_NAME
from app.modules.knowledge_base.domain.enums.recalculation_trigger import RecalculationTrigger
from app.modules.knowledge_base.domain.events.similarity_recalculation_requested import (
	SimilarityRecalculationRequested,
)
from app.shared.events.event_publisher import EventPublisher
from app.workers.jobs import JobQueue

logger = logging.getLogger(__name__)


class TriggerSimilarityRecalculationHandler:
	"""Starts the same pass the scheduler fires, on demand, without waiting for it.

	Enqueued rather than awaited. A full pass walks the entire corpus and writes a batch at a time;
	holding an HTTP request open for it would tie the run to a connection that a proxy, a browser
	or a laptop lid can close, and the run would carry on regardless with nobody left to tell. So
	the request's job ends at "accepted", and the outcome goes where every background outcome in
	this codebase goes -- the log.

	Refusing while one is already in flight, rather than queueing behind it, is the honest answer
	to what a second run would achieve: the pass recomputes the whole graph from the corpus as it
	stands, so one that starts a minute after another finishes produces the same rows again. The
	check here is a courtesy that turns the common case into a clear refusal; the runner guards
	itself as well, which is what actually prevents two passes, since anything checked before an
	enqueue can be overtaken by a schedule firing in between.

	Publishing SimilarityRecalculationRequested is the whole reason this handler records anything
	at all. It is the only moment in the pass's life at which an actor exists -- the run starts,
	finishes and may fail long after this request is gone, with no CurrentUser to attribute any of
	it to -- so if the event is not published here, "who started this" is unanswerable afterwards.
	The events the runner publishes carry the outcome; this one carries the person.
	"""

	def __init__(self, runner: RecalculationRunner, job_queue: JobQueue, event_publisher: EventPublisher) -> None:
		self.runner = runner
		self.job_queue = job_queue
		self.event_publisher = event_publisher

	async def handle(self, command: TriggerSimilarityRecalculationCommand) -> None:
		if self.runner.is_running:
			raise RecalculationAlreadyRunning()

		logger.info("Full similarity graph recalculation requested by %s.", command.actor_id)
		# The trigger is bound into the job here rather than defaulted on the runner, so a pass can
		# never report a door it did not come through.
		await self.job_queue.enqueue(
			partial(self.runner.run, RecalculationTrigger.MANUAL), name=SIMILARITY_RECALCULATION_JOB_NAME
		)
		# Published after the enqueue, so the announcement follows the act it announces -- the same
		# order as publishing after a commit, applied to the only durable step this handler has.
		await self.event_publisher.publish(
			SimilarityRecalculationRequested(occurred_at=command.requested_at, actor_id=command.actor_id)
		)
