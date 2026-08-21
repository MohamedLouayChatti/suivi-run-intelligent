from __future__ import annotations

from datetime import UTC, datetime

from app.modules.auth.application.commands.set_user_organizational_identity.command import (
	SetUserOrganizationalIdentityCommand,
)
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import RoleNotFound, UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.events.user_organizational_identity_changed import (
	UserOrganizationalIdentityChanged,
)
from app.modules.auth.domain.services.staffing_service import StaffingService
from app.shared.events.event_publisher import EventPublisher


class SetUserOrganizationalIdentityHandler:
	"""Restaffs a user, and does nothing at all when the request describes what they already are.

	The no-op returns early rather than committing and publishing, exactly as `SetUserRoleHandler`
	does: an event whose two sides are identical records an administrative act that did not
	happen, and would tell the user their assignment changed when nothing about it did.

	A combination the aggregate refuses -- a second primary, a Configuration engineer on AERO --
	propagates as the domain error it is, rather than being dropped the way the signup
	declaration is.  That fallback exists because the Clerk webhook has no one to report to and
	cannot be allowed to fail; an administrator making a deliberate assignment does have somewhere
	to see the refusal, and silently downgrading it would leave them believing it took effect.

	Staffing is also checked against the role the user already holds: a role that only means
	something for someone running an application cannot survive that application being taken
	away.  Validating role assignment alone would leave the rule escapable in one click from
	here, which is the opposite of an invariant.
	"""

	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, staffing_service: StaffingService) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.staffing_service = staffing_service

	async def handle(self, command: SetUserOrganizationalIdentityCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()

		previous_functional_team = user.functional_team
		previous_assignments = frozenset(user.application_assignments)
		if previous_functional_team == command.functional_team and previous_assignments == command.application_assignments:
			return UserDTO.from_user(user)

		user.update_organizational_identity(
			functional_team=command.functional_team,
			application_assignments=set(command.application_assignments),
		)

		# After the aggregate has accepted the new staffing, not before: what the role requires is
		# a question about the *resulting* assignments, and asking it of the old ones would refuse
		# the very edit that fixes an under-staffed user.  Nothing has been handed to the
		# repository yet, so a refusal here leaves the session untouched.
		role = await self.uow.roles.get_by_id(user.role_id)
		if role is None:
			raise RoleNotFound()
		self.staffing_service.ensure_staffed_for_role(user, role)

		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			UserOrganizationalIdentityChanged(
				user_id=user.id,
				previous_functional_team=previous_functional_team,
				new_functional_team=user.functional_team,
				previous_application_assignments=previous_assignments,
				new_application_assignments=frozenset(user.application_assignments),
				occurred_at=datetime.now(UTC),
				actor_id=command.actor_id,
			)
		)
		return UserDTO.from_user(user)
