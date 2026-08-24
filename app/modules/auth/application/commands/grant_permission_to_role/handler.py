from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.grant_permission_to_role.command import GrantPermissionToRoleCommand
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.exceptions import PermissionNotFound, RoleNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.role_permission_granted import RolePermissionGranted
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.modules.auth.domain.value_objects.permission_dependency_graph import PermissionDependencyGraph
from app.shared.events.event_publisher import EventPublisher


class GrantPermissionToRoleHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, authorization_service: AuthorizationService) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.authorization_service = authorization_service

	async def handle(self, command: GrantPermissionToRoleCommand) -> RoleDTO:
		role = await self.uow.roles.get_by_id(command.role_id)
		if role is None:
			raise RoleNotFound()
		permission = await self.uow.permissions.get_by_id(command.permission_id)
		if permission is None:
			raise PermissionNotFound()
		catalog = await self.uow.permissions.list()
		self.authorization_service.ensure_role_permission_may_be_granted(
			role,
			permission,
			PermissionDependencyGraph.from_permissions(catalog),
			{entry.id: entry.name for entry in catalog},
		)
		role.grant_permission(permission.id)
		await self.uow.roles.update(role)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(RolePermissionGranted(role_id=role.id, permission_id=permission.id, occurred_at=datetime.now(UTC), actor_id=command.actor_id))
		return RoleDTO.from_role(role)
