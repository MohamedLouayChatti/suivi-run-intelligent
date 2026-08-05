from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.status import Status
from app.shared.events.event import DomainEvent

@dataclass(frozen=True)
class TicketCreated(DomainEvent):
	ticket_id: UUID
	title: str
	description: str
	status: Status
	priority: Priority
	created_at: datetime
	assignee_id: UUID
	category: Category
	functional_team: FunctionalTeam
	actor_id: UUID
