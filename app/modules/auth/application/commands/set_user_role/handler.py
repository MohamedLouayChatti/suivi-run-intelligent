from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.set_user_role.command import SetUserRoleCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import RoleNotFound, UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.user_role_changed import UserRoleChanged
from app.modules.auth.domain.services.staffing_service import StaffingService
from app.shared.events.event_publisher import EventPublisher


class SetUserRoleHandler:
	"""Replaces the user's one role, and does nothing at all when it is already theirs.

	The no-op case returns early rather than committing and publishing: a `UserRoleChanged`
	whose previous and new role are the same records an administrative act that did not
	happen, and would notify the user that their role changed when nothing about their
	access did.

	A role that only means something for someone running an application is refused to a user
	who runs none (`StaffingService`).  Checked here rather than inside `User` because the rule
	spans both aggregates -- the requirement is declared on the Role, the staffing lives on the
	User -- which is the same boundary `AuthorizationService` exists to sit on.

	Setting a role also clears every permission exception the user carried, which `User.set_role`
	owns; the exceptions swept away are captured here only so the published event can carry them.
	"""

	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, staffing_service: StaffingService) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.staffing_service = staffing_service

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

		self.staffing_service.ensure_staffed_for_role(user, role)
		discarded_direct = frozenset(user.direct_permission_ids)
		discarded_revoked = frozenset(user.revoked_permission_ids)
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
				discarded_direct_permission_ids=discarded_direct,
				discarded_revoked_permission_ids=discarded_revoked,
				occurred_at=datetime.now(UTC),
				actor_id=command.actor_id,
			)
		)
		return UserDTO.from_user(user)
