from __future__ import annotations

from app.modules.ticket_management.application.commands.create_ticket.command import CreateTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated


class CreateTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: CreateTicketCommand) -> TicketDetailDTO:
		ticket = Ticket.create(
			id=command.ticket_id,
			title=command.title,
			description=command.description,
			priority=command.priority,
			created_at=command.created_at,
			application=command.application,
			assignee_id=command.assignee_id,
			category=command.category,
			functional_team=command.functional_team,
			genergy_id=command.genergy_id,
			oceane_id=command.oceane_id,
			jira_id=command.jira_id,
			jira_delivery_date=command.jira_delivery_date,
			requires_jira=command.requires_jira,
			operational_highlight=command.operational_highlight,
			offer=command.offer,
			version=command.version,
			element=command.element,
			vio_app=command.vio_app,
		)
		await self.uow.tickets.add(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketCreated(
				ticket_id=ticket.id,
				title=ticket.title,
				description=ticket.description,
				status=ticket.status,
				priority=ticket.priority,
				assignee_id=ticket.assignee_id,
				category=ticket.category,
				functional_team=ticket.functional_team,
				occurred_at=ticket.created_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
