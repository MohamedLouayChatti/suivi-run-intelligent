from __future__ import annotations

from dataclasses import dataclass

from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class GetApplicationInsightsQuery:
	application: Application
	time_range: TimeRange
