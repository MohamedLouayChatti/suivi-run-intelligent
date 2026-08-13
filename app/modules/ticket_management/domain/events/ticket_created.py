from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.status import Status
from app.shared.events.event import DomainEvent

@dataclass(frozen=True)
class TicketCreated(DomainEvent):
	"""`application`, `genergy_id` and `oceane_id` are here for Knowledge Base's similarity
	pipeline: it scopes candidate search to one application, and resolves references cited in a
	description ("suite ticket INC001010948992") against other tickets' genergy_id.
	"""

	ticket_id: UUID
	title: str
	description: str
	status: Status
	priority: Priority
	assignee_id: UUID
	category: Category
	functional_team: FunctionalTeam
	application: Application
	genergy_id: str | None = None
	oceane_id: str | None = None
