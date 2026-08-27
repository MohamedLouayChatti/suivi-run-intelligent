from __future__ import annotations

from dataclasses import dataclass

from app.modules.analytics.domain.enums.health_level import HealthLevel
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class ApplicationHealthBecameCritical(DomainEvent):
	"""An application's live signals crossed into CRITICAL against its own cached baseline.

	Published only on the transition, never on a re-check that finds an application already
	critical -- repeating it on every qualifying ticket event thereafter would turn one incident
	into a stream of identical notifications. `actor_id` is always `None` (the inherited
	default): this is a background-computed outcome of a reactive check, not a person's action,
	the same precedent as `SimilarityGraphRecalculated`/`SimilarityGraphRecalculationFailed`.
	"""

	application: Application
	previous_health_level: HealthLevel
	active_tickets: int
	avg_resolution_hours: float
	active_count_critical_threshold: float
	resolution_hours_critical_threshold: float
