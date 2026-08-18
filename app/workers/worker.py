from __future__ import annotations

import asyncio
import logging

from app.workers.handlers import run_job
from app.workers.jobs import Job, JobQueue

logger = logging.getLogger(__name__)


class InProcessJobRunner(JobQueue):
	"""Runs jobs as asyncio tasks on the API process's own event loop.

	Not a worker process, and the distinction is worth being precise about: this takes work off the
	*request*, not off the machine. That suits I/O-bound jobs, which spend their time waiting on
	sockets and interleave with request handling for free, and makes this the wrong home for
	CPU-bound work, which would block the very loop the API is served on.

	What it deliberately does not provide: durability, retries, or backpressure. A job is lost if
	the process stops, so only work that is recomputable and losable belongs here. Replacing this
	with a broker-backed adapter is a new JobQueue implementation plus a change to the singleton at
	the bottom of this file -- no caller changes, which is the point of the port.

	Tasks are held in a set for the whole of their lives. asyncio keeps only a weak reference to a
	running task, so one that nothing else holds can be garbage-collected mid-flight; the set is
	what stops a job vanishing silently, not bookkeeping.
	"""

	def __init__(self) -> None:
		self._tasks: set[asyncio.Task[None]] = set()

	async def enqueue(self, job: Job, *, name: str) -> None:
		task = asyncio.create_task(run_job(job, name), name=name)
		self._tasks.add(task)
		# Discards on completion as well as on cancellation, so the set tracks what is genuinely in
		# flight rather than growing for the lifetime of the process.
		task.add_done_callback(self._tasks.discard)

	async def shutdown(self) -> None:
		"""Cancels whatever is still running, and returns once every task has finished unwinding.

		Cancel rather than drain, chosen deliberately: an in-flight job is doing recomputable work
		that its own failure policy already treats as droppable, while draining would make every
		shutdown -- including every development reload -- wait on remote services.

		It still awaits the cancelled tasks, because cancellation is a request rather than an event:
		returning while they are mid-unwind would leave database sessions unclosed exactly as the
		engine is being disposed.
		"""
		if not self._tasks:
			return

		pending = list(self._tasks)
		logger.info("Cancelling %d in-flight background job(s) at shutdown.", len(pending))
		for task in pending:
			task.cancel()
		await asyncio.gather(*pending, return_exceptions=True)


# One runner for the process, mirroring `storage_service` in app/shared/storage/: the set of
# in-flight tasks is process-wide state, so a second instance would be a second, unwatched set of
# them that nothing cancels at shutdown.
job_queue: JobQueue = InProcessJobRunner()
