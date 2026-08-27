from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.modules.analytics.domain.enums.health_level import HealthLevel
from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class ApplicationHealthStatus:
	"""The last known tier for an application, persisted so a reactive check can tell a
	transition into CRITICAL from a re-check that finds it already there -- the notification
	fires on the former only."""

	application: Application
	health_level: HealthLevel
	active_tickets: int
	avg_resolution_hours: float
	updated_at: datetime
