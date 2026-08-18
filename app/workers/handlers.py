from __future__ import annotations

import asyncio
import logging

from app.workers.jobs import Job

logger = logging.getLogger(__name__)


async def run_job(job: Job, name: str) -> None:
	"""The outcome policy every background job shares, in one place because every one of them needs
	it: a job has no caller left to raise to.

	An exception escaping here would reach the event loop's default handler and surface, if at all,
	as an "exception was never retrieved" warning whenever the task object is garbage-collected --
	which is to say a failure would be effectively invisible. So failures are logged against the
	job's name and go no further. It is the same "log and carry on" contract InMemoryEventBus
	applies to event handlers, for the same reason: nothing downstream can act on the exception, and
	the alternative is losing it.

	Cancellation is not a failure and is re-raised rather than logged as one. It is how shutdown
	stops in-flight work, and swallowing a CancelledError would defeat the cancellation that asked
	for it.
	"""
	try:
		await job()
	except asyncio.CancelledError:
		logger.info("Background job %s was cancelled before it finished.", name)
		raise
	except Exception:
		logger.exception("Background job %s failed.", name)
