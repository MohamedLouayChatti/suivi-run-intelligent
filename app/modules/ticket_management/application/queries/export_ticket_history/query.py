from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class ExportTicketHistoryQuery:
	application: Application | None = None
	status: Status | None = None
	category: Category | None = None
	assignee_id: UUID | None = None
	search: str = ""
	date_from: date | None = None
	date_to: date | None = None
	allowed_applications: frozenset[Application] | None = None
