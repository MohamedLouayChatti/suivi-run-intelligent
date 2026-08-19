from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

# A job is a zero-argument async callable: everything it needs is already bound into it by whoever
# enqueued it. That is what keeps this package free of any module -- the queue never composes a
# job's dependencies, so it never has to know which module the work belongs to, and a module never
# has to register anything with it. The dependency runs one way, the same way app/shared/storage/
# is depended upon and depends on nothing.
Job = Callable[[], Awaitable[None]]


class JobQueue(ABC):
	"""Port for work that must leave the request that triggered it.

	`enqueue` is async even though the in-process adapter has nothing to await: a broker-backed
	implementation writes over the network, and a port shaped around the cheapest implementation is
	one that cannot later be swapped for the expensive one.

	Enqueuing deliberately returns no handle -- no id, no future, no result. There is nothing to
	wait on and no way to ask whether the job finished, which is a constraint rather than an
	omission: work whose outcome a caller needs is not background work and does not belong here.
	"""

	@abstractmethod
	async def enqueue(self, job: Job, *, name: str) -> None:
		"""Hand `job` off to run outside the caller's control flow.

		`name` identifies it in logs, which is the only place a background job is ever observed --
		it has no response to appear in and no caller left to raise to.
		"""
		raise NotImplementedError

	@abstractmethod
	async def shutdown(self) -> None:
		"""Release whatever the queue is holding as the process stops. On the port because every
		implementation has something to end -- in-flight tasks here, a broker connection pool for
		anything backed by one."""
		raise NotImplementedError


@dataclass(frozen=True, slots=True)
class WeeklySchedule:
	"""When a recurring job fires: a set of weekdays, one time of day, one timezone.

	Deliberately the smallest shape that expresses a recurring maintenance window, not a general
	calendar. One time of day for the whole set means "Tuesday and Friday at 20:00" is a single
	value, while "Tuesday at 20:00 and Friday at 03:00" is not expressible -- which is the trade
	that keeps this a schedule rather than a scheduling platform.

	Carries no validation of its own: the fields are what a cron trigger needs, and whoever builds
	one owns the invariants over them (a domain value object, in the one module that has such a
	schedule today). Weekdays are the three-letter lowercase codes cron vocabulary already uses,
	so no mapping table sits between this and the scheduler.
	"""

	days_of_week: tuple[str, ...]
	hour: int
	minute: int
	timezone: str


class JobScheduler(ABC):
	"""Port for work that recurs on a clock rather than being triggered by something that happened.

	The companion of JobQueue, and separate from it on purpose: enqueuing says "run this, once,
	soon", while scheduling says "run this whenever the calendar says so, until told otherwise".
	A job registered here is identified by a stable `name` for its whole life, because the point
	of the identity is to be able to come back later and change when it fires.

	Like JobQueue, this knows nothing about any module: it is handed an already-composed zero-
	argument coroutine and a schedule, never the ingredients of either.

	Deliberately absent: any "run it now" method. That is JobQueue's job, and routing a manual
	trigger through the scheduler would make the immediate run share the recurring one's slot,
	misfire policy and bookkeeping for no gain.
	"""

	@abstractmethod
	async def register(self, job: Job, *, name: str, schedule: WeeklySchedule, enabled: bool) -> None:
		"""Register `job` under `name`, replacing any previous registration of that name.

		`enabled` is separate from `schedule` because the two answer different questions and are
		configured independently: the schedule is *when* it would fire, `enabled` is whether it
		fires at all. A disabled job keeps its trigger, so re-enabling it needs no schedule to be
		supplied again.
		"""
		raise NotImplementedError

	@abstractmethod
	async def reschedule(self, name: str, *, schedule: WeeklySchedule, enabled: bool) -> None:
		"""Point an already-registered job at a new schedule, taking effect immediately.

		Existing in the first place is what keeps a configuration change from needing a restart --
		which is the whole reason a schedule is stored in a database rather than in code.
		"""
		raise NotImplementedError

	@abstractmethod
	def next_run_at(self, name: str) -> datetime | None:
		"""When `name` is next due, or None if it is disabled or was never registered.

		Sync, and the one read on this port: it answers from the scheduler's own state without
		touching anything remote, which is what makes it cheap enough for an ordinary read
		endpoint to include.
		"""
		raise NotImplementedError

	@abstractmethod
	async def start(self) -> None:
		"""Begin firing registered jobs. Called once, after every registration, at startup."""
		raise NotImplementedError

	@abstractmethod
	async def shutdown(self) -> None:
		"""Stop firing and release whatever the scheduler is holding as the process stops."""
		raise NotImplementedError
