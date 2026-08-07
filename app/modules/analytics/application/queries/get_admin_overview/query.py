from __future__ import annotations

from dataclasses import dataclass

from app.modules.analytics.application.support.time_range import TimeRange


@dataclass(frozen=True)
class GetAdminOverviewQuery:
	time_range: TimeRange
