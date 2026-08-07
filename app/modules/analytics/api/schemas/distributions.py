from __future__ import annotations

from pydantic import BaseModel

from app.modules.analytics.application.dto.distributions_dto import DistributionsDTO
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status


class DistributionsResponse(BaseModel):
	by_status: dict[Status, int]
	by_category: dict[Category, int]
	by_priority: dict[Priority, int]

	@classmethod
	def from_dto(cls, distributions: DistributionsDTO) -> DistributionsResponse:
		return cls(
			by_status=distributions.by_status,
			by_category=distributions.by_category,
			by_priority=distributions.by_priority,
		)
