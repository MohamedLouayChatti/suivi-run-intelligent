from __future__ import annotations

from app.modules.ticket_management.application.commands.update_jira_details.command import UpdateJiraDetailsCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.jira_details_updated import JiraDetailsUpdated


class UpdateJiraDetailsHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: UpdateJiraDetailsCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		ticket.update_jira_details(
			requires_jira=command.requires_jira,
			jira_id=command.jira_id,
			jira_delivery_date=command.jira_delivery_date,
			updated_at=command.updated_at,
		)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			JiraDetailsUpdated(
				ticket_id=ticket.id,
				requires_jira=ticket.requires_jira,
				jira_id=ticket.jira_id,
				jira_delivery_date=ticket.jira_delivery_date,
				occurred_at=command.updated_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
