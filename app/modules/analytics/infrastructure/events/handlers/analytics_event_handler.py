from __future__ import annotations

import logging
from uuid import UUID

from app.modules.analytics.application.commands.check_application_health.command import (
	CheckApplicationHealthCommand,
)
from app.modules.analytics.application.commands.check_application_health.handler import (
	CheckApplicationHealthHandler,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_admin_analytics_read_repository import (
	SqlAlchemyAdminAnalyticsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.modules.ticket_management.domain.events.ticket_restored import TicketRestored
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)
from app.shared.database.session import create_session
from app.shared.events.event import DomainEvent
from app.shared.events.event_publisher import EventPublisher
from app.shared.events.handler import EventHandler
from app.workers.jobs import Job, JobQueue

logger = logging.getLogger(__name__)

# The four events that can move a ticket into or out of an application's active population
# without themselves carrying which Application it belongs to -- TicketCreated is the only one
# of the five that does, so it is the only one that skips the lookup below.
_TICKET_ID_ONLY_EVENTS = (TicketStatusChanged, TicketArchived, TicketRestored, TicketTransferred)


class AnalyticsEventHandler(EventHandler):
	"""Subscribed to TicketCreated, TicketStatusChanged, TicketArchived, TicketRestored and
	TicketTransferred -- the five ticket events that can move an application's live health
	signals enough to change its tier.

	Does no DB work itself, exactly like Knowledge Base's own event handler and for the same
	reason: a 30-day-window health check depends on the whole application's current state, which
	one ticket rarely moves, so nothing in the request that triggered it is waiting on the
	result. The check is bound into a closure and enqueued on the shared JobQueue instead.
	"""

	def __init__(self, event_publisher: EventPublisher, job_queue: JobQueue) -> None:
		self.event_publisher = event_publisher
		self.job_queue = job_queue

	async def handle(self, event: DomainEvent) -> None:
		if isinstance(event, TicketCreated):
			ticket_id, application = event.ticket_id, event.application
		elif isinstance(event, _TICKET_ID_ONLY_EVENTS):
			ticket_id, application = event.ticket_id, None
		else:
			logger.warning("AnalyticsEventHandler received unexpected event type %s", type(event).__name__)
			return

		await self.job_queue.enqueue(
			self._check_health_job(ticket_id, application),
			name=f"analytics.check_health[{ticket_id}]",
		)

	def _check_health_job(self, ticket_id: UUID, application: Application | None) -> Job:
		async def check_health() -> None:
			resolved_application = application
			if resolved_application is None:
				# The same cross-module lookup Notifications' RecipientResolver.get_ticket
				# already uses: Ticket Management's Application-layer read repository, never
				# its ORM model.
				session = create_session()
				try:
					ticket = await SqlAlchemyTicketReadRepository(session).get_ticket(ticket_id)
				finally:
					await session.close()
				if ticket is None:
					logger.warning(
						"AnalyticsEventHandler: ticket %s no longer exists, skipping health check.", ticket_id
					)
					return
				resolved_application = ticket.application

			uow = SqlAlchemyUnitOfWork()
			try:
				handler = CheckApplicationHealthHandler(
					signals=SqlAlchemyAdminAnalyticsReadRepository(uow.session),
					uow=uow,
					event_publisher=self.event_publisher,
				)
				await handler.handle(CheckApplicationHealthCommand(application=resolved_application))
			except Exception:
				await uow.rollback()
				raise
			finally:
				await uow.close()

		return check_health
