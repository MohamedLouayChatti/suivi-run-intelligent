from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.analytics.application.dto.engineer_activity_dto import EngineerActivityDTO
from app.modules.analytics.application.support.time_range import DateWindow
from app.modules.ticket_management.domain.enums.application import Application


class EngineerActivityReadRepository(ABC):
	"""One engineer's workload profile, narrowed to a set of applications.

	Its own seam rather than a method on either neighbouring repository, because it is scoped
	by assignee *and* by application and neither of those is: AdminAnalyticsReadRepository is
	never scoped by application (its callers hold the breadth permission outright), and
	PersonalAnalyticsReadRepository is never scoped by application either -- an assignee sees
	their own tickets regardless of where they are assigned. Asking about a *colleague* is the
	case where both scopes apply at once: who did the work, and how much of it the caller is
	allowed to see.
	"""

	@abstractmethod
	async def get_engineer_activity(
		self, engineer_id: UUID, applications: frozenset[Application] | None, window: DateWindow
	) -> EngineerActivityDTO:
		"""`applications` of None means unrestricted -- the caller holds the breadth permission."""
		raise NotImplementedError
