from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.workers.handlers import run_job
from app.workers.jobs import Job, JobQueue, JobScheduler, WeeklySchedule

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


# A run missed while the process was down is skipped rather than made up. APScheduler decides that
# with `misfire_grace_time`: a firing later than this many seconds past its due time is dropped.
# The value is small on purpose -- the jobs scheduled here are deliberately placed outside working
# hours, so a restart at 09:00 the next morning must not immediately start the expensive pass that
# was due at 20:00. Nothing is lost by skipping: the work is periodic maintenance, and the next
# scheduled run does exactly what the missed one would have.
_MISFIRE_GRACE_SECONDS = 60


class APSchedulerRunner(JobScheduler):
	"""JobScheduler backed by APScheduler's AsyncIOScheduler, on the API process's own event loop.

	The same trade InProcessJobRunner makes, for the same reason: this is a clock attached to the
	API process, not a worker service. There is no job store -- schedules are held in memory and
	re-registered from their persisted configuration at every startup, which is why the
	configuration lives in an ordinary table owned by the module that owns the job rather than in
	one of APScheduler's own persistent stores. A job store would be a second, competing source of
	truth about when things run, and the one in the database is the one an administrator edits.

	One process is assumed. Running the API under several worker processes would give each its own
	scheduler and fire every job once per process; that is the same constraint InProcessJobRunner
	already carries, and the same answer applies -- a broker-backed implementation of these two
	ports is what changes it, not a flag here.

	Every job is wrapped in `run_job`, so scheduled work and enqueued work share one outcome
	policy: a failure is logged against the job's name and goes no further, leaving the schedule
	intact so the next firing is unaffected by this one having failed.
	"""

	def __init__(self) -> None:
		self._scheduler = AsyncIOScheduler()

	async def register(self, job: Job, *, name: str, schedule: WeeklySchedule, enabled: bool) -> None:
		self._scheduler.add_job(
			run_job,
			trigger=self._trigger(schedule),
			args=(job, name),
			id=name,
			name=name,
			replace_existing=True,
			# One at a time, and a firing that arrives while the previous one is still running is
			# dropped rather than queued behind it. Both matter for a long pass: overlapping runs
			# would recompute the same rows against each other, and a backlog of them would still
			# be working through last week's schedule days later.
			max_instances=1,
			coalesce=True,
			misfire_grace_time=_MISFIRE_GRACE_SECONDS,
		)
		if not enabled:
			self._scheduler.pause_job(name)
		logger.info(
			"Scheduled job %s registered (%s at %02d:%02d %s).",
			name, ",".join(schedule.days_of_week), schedule.hour, schedule.minute, schedule.timezone,
		)

	async def reschedule(self, name: str, *, schedule: WeeklySchedule, enabled: bool) -> None:
		# The trigger is replaced even when the job is about to be paused, so that a schedule
		# edited while disabled is the one that takes effect when it is enabled again -- otherwise
		# re-enabling would silently resurrect whatever times were configured before.
		self._scheduler.reschedule_job(name, trigger=self._trigger(schedule))
		if not enabled:
			self._scheduler.pause_job(name)
		logger.info(
			"Scheduled job %s rescheduled (%s at %02d:%02d %s, enabled=%s).",
			name, ",".join(schedule.days_of_week), schedule.hour, schedule.minute, schedule.timezone, enabled,
		)

	def next_run_at(self, name: str) -> datetime | None:
		job = self._scheduler.get_job(name)
		# A paused job reports no next run time, which is exactly the answer a disabled schedule
		# should give -- no separate branch needed for it.
		return job.next_run_time if job is not None else None

	async def start(self) -> None:
		self._scheduler.start()

	async def shutdown(self) -> None:
		"""Stops the clock and cancels whatever it had in flight.

		`wait=False` matches InProcessJobRunner's cancel-rather-than-drain policy: APScheduler's
		asyncio executor cancels its pending tasks, and a scheduled pass is recomputable work whose
		own failure policy already treats it as droppable. Guarded on `running` because shutting
		down a scheduler that never started raises rather than being a no-op, and startup is
		allowed to fail before it gets that far.

		The yield afterwards is not a delay for its own sake. AsyncIOScheduler does not stop inside
		`shutdown()` -- it schedules the teardown onto the event loop and returns immediately -- so
		without giving the loop a turn this would report having shut down a scheduler that is still
		running, and the timer and executors would survive as long as the loop did.
		"""
		if not self._scheduler.running:
			return
		self._scheduler.shutdown(wait=False)
		await asyncio.sleep(0)

	@staticmethod
	def _trigger(schedule: WeeklySchedule) -> CronTrigger:
		# The timezone is handed over as a string rather than as a resolved tzinfo: APScheduler
		# resolves it with whichever library its version is built on, and passing an object built
		# by the other one is rejected. Validity is already established upstream, by whoever built
		# the WeeklySchedule.
		return CronTrigger(
			day_of_week=",".join(schedule.days_of_week),
			hour=schedule.hour,
			minute=schedule.minute,
			timezone=schedule.timezone,
		)


# One runner for the process, mirroring `storage_service` in app/shared/storage/: the set of
# in-flight tasks is process-wide state, so a second instance would be a second, unwatched set of
# them that nothing cancels at shutdown.
job_queue: JobQueue = InProcessJobRunner()

# Same reasoning, and the same lifecycle: the registered schedules are process-wide state, and a
# second scheduler would be a second clock firing the same jobs.
job_scheduler: JobScheduler = APSchedulerRunner()
