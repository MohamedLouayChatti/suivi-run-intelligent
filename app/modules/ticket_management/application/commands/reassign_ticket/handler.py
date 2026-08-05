from __future__ import annotations

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.commands.reassign_ticket.command import ReassignTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import AssigneeNotAuthorized, AssigneeNotFound, TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_reassigned import TicketReassigned


class ReassignTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, user_repository: UserReadRepository) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.user_repository = user_repository

	async def handle(self, command: ReassignTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()

		candidate = await self.user_repository.get_user(command.assignee_id)
		if candidate is None:
			raise AssigneeNotFound()
		if candidate.functional_team.value != ticket.functional_team.value:
			raise AssigneeNotAuthorized()
		if not any(assignment.application.value == ticket.application.value for assignment in candidate.application_assignments):
			raise AssigneeNotAuthorized()

		ticket.reassign(command.assignee_id, command.reassigned_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketReassigned(
				ticket_id=ticket.id,
				assignee_id=command.assignee_id,
				occurred_at=command.reassigned_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
