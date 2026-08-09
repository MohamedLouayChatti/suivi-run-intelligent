from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class JiraDetailsUpdated(DomainEvent):
	ticket_id: UUID
	requires_jira: bool
	jira_id: str | None
	jira_delivery_date: date | None
