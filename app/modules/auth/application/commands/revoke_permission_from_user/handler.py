from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.revoke_permission_from_user.command import RevokePermissionFromUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import PermissionNotFound, RoleNotFound, UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.modules.auth.domain.value_objects.permission_dependency_graph import PermissionDependencyGraph
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
		role = await self.uow.roles.get_by_id(user.role_id)
		if role is None:
			raise RoleNotFound()
		catalog = await self.uow.permissions.list()
		dependencies = PermissionDependencyGraph.from_permissions(catalog)
		self.authorization_service.ensure_direct_permission_may_be_revoked(user, permission.id, role, dependencies)

		# Everything that depended on this permission comes away in the same act, since leaving
		# it held-but-unusable is precisely the state the dependency relation exists to prevent.
		# `User.revoke_permission` records each as an exception rather than merely dropping a
		# direct grant, which is what makes this reach a dependent inherited from the role.
		effective = self.authorization_service.resolve_permissions(user, role, dependencies)
		revoked = self.authorization_service.cascade_for_revocation(permission.id, held=effective, dependencies=dependencies)
		for permission_id in revoked:
			user.revoke_permission(permission_id)
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(PermissionRevokedFromUser(user_id=user.id, permission_ids=revoked, occurred_at=datetime.now(UTC), actor_id=command.actor_id))
		return UserDTO.from_user(user)
