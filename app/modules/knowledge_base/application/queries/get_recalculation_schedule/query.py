from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetRecalculationScheduleQuery:
	"""Read the configured full-recalculation schedule and its current scheduler state.

	Deliberately parameterless: there is one schedule for the installation, so there is nothing to
	select it by. It is still a query object rather than a bare handler call, so this endpoint
	reads like every other one in the codebase.
	"""
