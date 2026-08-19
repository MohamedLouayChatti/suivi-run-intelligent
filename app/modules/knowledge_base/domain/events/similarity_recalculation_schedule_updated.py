from __future__ import annotations

from dataclasses import dataclass

from app.modules.knowledge_base.domain.enums.weekday import Weekday
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class SimilarityRecalculationScheduleUpdated(DomainEvent):
	"""An administrator changed when -- or whether -- the whole similarity graph is rebuilt.

	The only configuration change in this codebase held in a table rather than in code, and the one
	whose effect nobody can see directly: what it moves is a background pass that runs outside
	working hours, so a change to it stays invisible until an engineer notices that similar-incident
	results have stopped improving. That is exactly the kind of change worth announcing rather than
	only logging.

	Carries the whole schedule and not the one it replaced, mirroring JiraDetailsUpdated rather
	than PriorityChanged: the fields are meaningless apart from each other, so a diff of five
	values reads worse than the value that now applies -- and the value it replaced is the previous
	entry in the audit log.

	days_of_week is a tuple in week order, not the frozenset the domain holds. A set has no order,
	and this value ends up in a JSONB payload and in notification text, both of which would
	otherwise vary between two events recording an identical schedule.
	"""

	enabled: bool
	days_of_week: tuple[Weekday, ...]
	hour: int
	minute: int
	timezone: str
