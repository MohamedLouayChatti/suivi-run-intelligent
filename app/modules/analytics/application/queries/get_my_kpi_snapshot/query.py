from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

# "This week" on the Dashboard is a fixed trailing 7-day window, not one of the
# Analytics page's selectable TimeRange values -- there's no time-range control on that
# page at all.
PERSONAL_KPI_WINDOW_DAYS = 7


@dataclass(frozen=True)
class GetMyKpiSnapshotQuery:
	assignee_id: UUID
