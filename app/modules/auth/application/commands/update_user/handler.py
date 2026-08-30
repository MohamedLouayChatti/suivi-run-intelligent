from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.update_user.command import UpdateUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.user_updated import UserUpdated
from app.shared.events.event_publisher import EventPublisher


class UpdateUserHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: UpdateUserCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()
		if command.email is not None:
			user.email = command.email
		if command.first_name is not None:
			user.first_name = command.first_name
		if command.last_name is not None:
			user.last_name = command.last_name
		if command.avatar_url is not None:
			user.avatar_url = command.avatar_url
		if command.functional_team is not None or command.application_assignments is not None:
			user.update_organizational_identity(
				functional_team=command.functional_team,
				application_assignments=None if command.application_assignments is None else set(command.application_assignments),
			)
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(UserUpdated(user_id=user.id, occurred_at=datetime.now(UTC), actor_id=command.actor_id))
		return UserDTO.from_user(user)
