from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.domain.enums.application import Application as TicketApplication
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam as TicketFunctionalTeam
from app.shared.security.current_user import CurrentUser

TicketReadRepositoryScope = Callable[[], AbstractAsyncContextManager[TicketReadRepository]]
UserReadRepositoryScope = Callable[[], AbstractAsyncContextManager[UserReadRepository]]

ADMIN_ROLE_NAME = "Admin"


def parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None


def has_application_assignment(current_user: CurrentUser, application: TicketApplication) -> bool:
	return any(
		assignment.application.value == application.value
		for assignment in current_user.application_assignments
	)


def is_same_functional_team(current_user: CurrentUser, functional_team: TicketFunctionalTeam) -> bool:
	return current_user.functional_team.value == functional_team.value


async def is_admin(user_repository_scope: UserReadRepositoryScope, current_user: CurrentUser) -> bool:
	async with user_repository_scope() as users:
		roles = await users.get_user_roles(current_user.id)
	return any(role.name == ADMIN_ROLE_NAME for role in roles)
