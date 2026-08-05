from __future__ import annotations

from app.modules.auth.application.commands.revoke_permission_from_user.command import RevokePermissionFromUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import PermissionNotFound, RoleNotFound, UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.shared.events.event_publisher import EventPublisher


class RevokePermissionFromUserHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, authorization_service: AuthorizationService) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.authorization_service = authorization_service

	async def handle(self, command: RevokePermissionFromUserCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()
		permission = await self.uow.permissions.get_by_id(command.permission_id)
		if permission is None:
			raise PermissionNotFound()
		roles = []
		for role_id in user.role_ids:
			role = await self.uow.roles.get_by_id(role_id)
			if role is None:
				raise RoleNotFound()
			roles.append(role)
		self.authorization_service.ensure_direct_permission_may_be_revoked(user, permission.id, roles)
		user.revoke_permission(permission.id)
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(PermissionRevokedFromUser(user_id=user.id, permission_id=permission.id, actor_id=command.actor_id))
		return UserDTO.from_user(user)
