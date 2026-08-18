from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

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
