from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.deactivate_user.command import DeactivateUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.user_deactivated import UserDeactivated
from app.shared.events.event_publisher import EventPublisher


class DeactivateUserHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: DeactivateUserCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()
		user.deactivate()
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(UserDeactivated(user_id=user.id, occurred_at=datetime.now(UTC), actor_id=command.actor_id))
		return UserDTO.from_user(user)
