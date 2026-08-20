from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.set_user_role.command import SetUserRoleCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import RoleNotFound, UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.user_role_changed import UserRoleChanged
from app.shared.events.event_publisher import EventPublisher


class SetUserRoleHandler:
	"""Replaces the user's one role, and does nothing at all when it is already theirs.

	The no-op case returns early rather than committing and publishing: a `UserRoleChanged`
	whose previous and new role are the same records an administrative act that did not
	happen, and would notify the user that their role changed when nothing about their
	access did.
	"""

	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: SetUserRoleCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()
		role = await self.uow.roles.get_by_id(command.role_id)
		if role is None:
			raise RoleNotFound()

		previous_role_id = user.role_id
		if previous_role_id == role.id:
			return UserDTO.from_user(user)

		user.set_role(role.id)
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			UserRoleChanged(
				user_id=user.id,
				previous_role_id=previous_role_id,
				new_role_id=role.id,
				occurred_at=datetime.now(UTC),
				actor_id=command.actor_id,
			)
		)
		return UserDTO.from_user(user)
