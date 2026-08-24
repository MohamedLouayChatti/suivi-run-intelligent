from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.revoke_permission_from_role.command import RevokePermissionFromRoleCommand
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.exceptions import PermissionNotFound, RoleNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.role_permission_revoked import RolePermissionRevoked
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.modules.auth.domain.value_objects.permission_dependency_graph import PermissionDependencyGraph
from app.shared.events.event_publisher import EventPublisher


class RevokePermissionFromRoleHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, authorization_service: AuthorizationService) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.authorization_service = authorization_service

	async def handle(self, command: RevokePermissionFromRoleCommand) -> RoleDTO:
		role = await self.uow.roles.get_by_id(command.role_id)
		if role is None:
			raise RoleNotFound()
		permission = await self.uow.permissions.get_by_id(command.permission_id)
		if permission is None:
			raise PermissionNotFound()
		catalog = await self.uow.permissions.list()

		# The role loses everything that depended on this permission alongside it. Scoped to
		# what the role itself holds -- a member who separately holds a dependent as a direct
		# grant is out of reach here, and repairing them would mean this write mutating every
		# member's aggregate; the closure applied when permissions are resolved covers that.
		revoked = self.authorization_service.cascade_for_revocation(
			permission.id,
			held=role.permission_ids,
			dependencies=PermissionDependencyGraph.from_permissions(catalog),
		)
		for permission_id in revoked:
			role.revoke_permission(permission_id)
		await self.uow.roles.update(role)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(RolePermissionRevoked(role_id=role.id, permission_ids=revoked, occurred_at=datetime.now(UTC), actor_id=command.actor_id))
		return RoleDTO.from_role(role)
