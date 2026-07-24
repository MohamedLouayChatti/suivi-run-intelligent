from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.element import Element
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.offer import Offer
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.version import Version


@dataclass(frozen=True)
class CreateTicketCommand:
	ticket_id: UUID
	title: str
	description: str
	priority: Priority
	created_at: datetime
	application: Application
	assignee_id: UUID
	category: Category
	functional_team: FunctionalTeam
	genergy_id: str | None = None
	oceane_id: str | None = None
	jira_id: str | None = None
	requires_jira: bool = False
	operational_highlight: bool = False
	offer: Offer | None = None
	version: Version | None = None
	element: Element | None = None
