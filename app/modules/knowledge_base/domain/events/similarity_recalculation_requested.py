from __future__ import annotations

from dataclasses import dataclass

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class SimilarityRecalculationRequested(DomainEvent):
	"""An administrator started a full recalculation by hand, outside the schedule.

	Carries nothing beyond the envelope, and the envelope is the entire point: actor_id is the one
	fact that exists here and nowhere else in the pass's life. By the time the run starts, finishes
	or fails there is no authenticated user left to attribute it to -- and a scheduled firing never
	had one -- so without this event, "who started this expensive out-of-band pass over the whole
	corpus" is a question the system cannot answer afterwards.

	It is also the one event in this module published with no commit behind it. The convention it
	appears to break exists to stop an announcement outliving a rolled-back transaction; here
	nothing is persisted at all, and the enqueue is the fact being recorded.
	"""
