from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class UpdateJiraDetailsCommand:
	ticket_id: UUID
	requires_jira: bool
	jira_id: str | None
	jira_delivery_date: date | None
	updated_at: datetime
	actor_id: UUID
