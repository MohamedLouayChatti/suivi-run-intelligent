from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.knowledge_base.domain.enums.recalculation_trigger import RecalculationTrigger


class RecalculationRunner(ABC):
	"""One full similarity graph recalculation, running at most one at a time.

	Exists as a port because three entry points need the *same* run, not three runs that happen to
	do the same thing: the scheduled firing, the administrator's "run now" and the end of a batch
	import. All three call `run` on one shared instance, which is what makes single-flight a
	property of the operation rather than a rule each caller has to remember.

	Deliberately thin, and still returns nothing -- what a pass does is
	RebuildSimilarityGraphCommand's business, and its outcome goes to the log and to the events it
	publishes, since a background run has no caller left to hand a report to.

	The one argument it does take says which door was used, and nothing about what to do. It is
	carried straight onto those events, so a reader can tell the routine Tuesday pass from one an
	administrator started thirty seconds ago -- a distinction the log had and the events would
	otherwise have lost. It cannot reach the pass itself: what a run computes is identical
	whichever way it was asked for, and it has to stay that way, or the graph would encode how its
	edges were requested.
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
	async def run(self, trigger: RecalculationTrigger) -> None:
		"""Recalculate the whole graph, unless a pass is already running -- in which case this
		returns without starting a second one.

		`trigger` is bound by whoever asks for the run, which is why this staying a one-argument
		coroutine costs its callers nothing: every one of them already hands the job runner a
		zero-argument closure, so binding one more value into it is where that value was always
		going to live.
		"""
		raise NotImplementedError
