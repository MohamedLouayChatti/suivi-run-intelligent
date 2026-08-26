from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class ListTicketsQuery:
	application: Application | None = None
	status: Status | None = None
	priority: Priority | None = None
	assignee_id: UUID | None = None
	exclude_assignee_id: UUID | None = None
	functional_team: FunctionalTeam | None = None
	category: Category | None = None
	operational_highlight: bool | None = None
	search: str = ""
	# Opt-in, not a default applied whenever `status` is unset: Dashboard also calls this query
	# with no status filter and expects every status back (its "recent tickets" style widgets),
	# so narrowing "no status chosen" to mean "active only" would silently change that caller's
	# results. The Tickets page is the one caller that asks for this.
	active_only: bool = False
	include_archived: bool = False
	limit: int = 100
	offset: int = 0
	allowed_applications: frozenset[Application] | None = None
