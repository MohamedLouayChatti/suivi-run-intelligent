from __future__ import annotations

from app.modules.auth.application.commands.create_user.command import CreateUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.events.user_created import UserCreated
from app.shared.events.event_publisher import EventPublisher


class CreateUserHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: CreateUserCommand) -> UserDTO:
		user = User.create(
			id=command.user_id,
			auth_provider_user_id=command.auth_provider_user_id,
			email=command.email,
			display_name=command.display_name,
		)
		await self.uow.users.add(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			UserCreated(
				user_id=user.id,
				auth_provider_user_id=user.auth_provider_user_id,
				email=user.email,
				display_name=user.display_name,
			)
		)
		return UserDTO.from_user(user)
