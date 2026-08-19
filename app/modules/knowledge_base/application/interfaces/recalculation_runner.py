from __future__ import annotations

from abc import ABC, abstractmethod


class RecalculationRunner(ABC):
	"""One full similarity graph recalculation, running at most one at a time.

	Exists as a port because two entry points need the *same* run, not two runs that happen to do
	the same thing: the scheduled firing and the administrator's "run now". Both call `run` on one
	shared instance, which is what makes single-flight a property of the operation rather than a
	rule each caller has to remember.

	Deliberately thin. It carries no arguments and returns nothing -- what a pass does is
	RebuildSimilarityGraphCommand's business, and its outcome goes to the log, since a background
	run has no caller left to hand a report to.
	"""

	@property
	@abstractmethod
	def is_running(self) -> bool:
		"""Whether a pass is in flight right now.

		Read by the trigger command, to refuse a manual run rather than silently drop it, and by
		the read endpoint, so an administrator can see that the button they pressed is doing
		something. It is a snapshot and nothing more: it can go stale the instant it is read, which
		is why `run` guards itself as well rather than trusting anyone who checked this first.
		"""
		raise NotImplementedError

	@abstractmethod
	async def run(self) -> None:
		"""Recalculate the whole graph, unless a pass is already running -- in which case this
		returns without starting a second one."""
		raise NotImplementedError
