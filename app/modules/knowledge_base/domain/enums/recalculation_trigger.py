from __future__ import annotations

from enum import StrEnum


class RecalculationTrigger(StrEnum):
	"""Which of the three doors into the full recalculation was used.

	Carried on the events a pass publishes, never consulted by the pass itself: every trigger runs
	the same handler over the same corpus with the same threshold and cap, so this says who opened
	the door and nothing about what happened behind it. Anything that made the pass *behave*
	differently per trigger would produce a graph whose edges depend on how they were requested.

	It earns its place on the failure event above all. "The Tuesday night pass failed" and "the
	pass an administrator started thirty seconds ago failed" need different reactions from whoever
	reads them, and without this they are the same record.
	"""

	SCHEDULED = "SCHEDULED"
	MANUAL = "MANUAL"
	BATCH_IMPORT = "BATCH_IMPORT"
