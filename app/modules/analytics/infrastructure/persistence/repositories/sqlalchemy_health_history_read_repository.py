from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.application.dto.ticket_lifecycle_event_dto import TicketLifecycleEventDTO
from app.modules.analytics.application.interfaces.health_history_read_repository import HealthHistoryReadRepository
from app.modules.analytics.infrastructure.persistence.query_helpers import DURATION_HOURS, resolved
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType
from app.modules.ticket_management.infrastructure.persistence.models.ticket_history_model import TicketHistoryModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel

# The four event types whose to_status (or lack of one) determines whether a ticket was active
# on a given day. PRIORITY_CHANGED/REASSIGNED/TRANSFERRED/JIRA_UPDATED/
# OPERATIONAL_HIGHLIGHT_CHANGED never move a ticket into or out of the active set, so they are
# excluded rather than filtered out later by reconstruct_daily_active_counts.
_LIFECYCLE_EVENT_TYPES = (
	TicketHistoryEventType.CREATED, TicketHistoryEventType.STATUS_CHANGED,
	TicketHistoryEventType.ARCHIVED, TicketHistoryEventType.RESTORED,
)


class SqlAlchemyHealthHistoryReadRepository(HealthHistoryReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_resolution_hours_history(self, application: Application) -> list[float]:
		stmt = select(DURATION_HOURS).where(TicketModel.application == application, resolved())
		rows = (await self.session.execute(stmt)).scalars().all()
		return [float(value) for value in rows if value is not None]

	async def get_ticket_lifecycle_events(self, application: Application) -> list[TicketLifecycleEventDTO]:
		# Not filtered by not_archived(): an archived ticket's own ARCHIVED entry is exactly
		# what marks when it left the active population, so excluding archived tickets here
		# would erase the one event that says so.
		stmt = (
			select(
				TicketHistoryModel.ticket_id, TicketHistoryModel.occurred_at,
				TicketHistoryModel.event_type, TicketHistoryModel.to_status,
			)
			.join(TicketModel, TicketModel.id == TicketHistoryModel.ticket_id)
			.where(TicketModel.application == application, TicketHistoryModel.event_type.in_(_LIFECYCLE_EVENT_TYPES))
			.order_by(TicketHistoryModel.ticket_id, TicketHistoryModel.occurred_at)
		)
		rows = (await self.session.execute(stmt)).all()
		return [
			TicketLifecycleEventDTO(
				ticket_id=row.ticket_id, occurred_at=row.occurred_at,
				event_type=row.event_type, to_status=row.to_status,
			)
			for row in rows
		]
