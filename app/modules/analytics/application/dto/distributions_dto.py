from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class DistributionsDTO:
	"""Ticket counts for the created-in-period cohort, grouped by their current
	status/category/priority. Every enum member is present, defaulting to 0."""

	by_status: dict[Status, int]
	by_category: dict[Category, int]
	by_priority: dict[Priority, int]
