from __future__ import annotations

from app.modules.auth.application.commands.revoke_role.command import RevokeRoleCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import RoleNotFound, UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.role_revoked_from_user import RoleRevokedFromUser
from app.shared.events.event_publisher import EventPublisher


class RevokeRoleHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: RevokeRoleCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()
		role = await self.uow.roles.get_by_id(command.role_id)
		if role is None:
			raise RoleNotFound()
		user.revoke_role(role.id)
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(RoleRevokedFromUser(user_id=user.id, role_id=role.id, actor_id=command.actor_id))
		return UserDTO.from_user(user)
