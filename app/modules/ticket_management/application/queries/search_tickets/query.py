from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class SearchTicketsQuery:
	term: str
	application: Application | None = None
	status: Status | None = None
	priority: Priority | None = None
	assignee_id: UUID | None = None
	functional_team: FunctionalTeam | None = None
	category: Category | None = None
	operational_highlight: bool | None = None
	include_archived: bool = False
	limit: int = 50
	offset: int = 0
