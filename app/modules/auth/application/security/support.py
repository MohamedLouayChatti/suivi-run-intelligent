from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.shared.security.current_user import CurrentUser

UserReadRepositoryScope = Callable[[], AbstractAsyncContextManager[UserReadRepository]]

ADMIN_ROLE_NAME = "Admin"


def parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None


async def is_admin(user_repository_scope: UserReadRepositoryScope, current_user: CurrentUser) -> bool:
	async with user_repository_scope() as users:
		roles = await users.get_user_roles(current_user.id)
	return any(role.name == ADMIN_ROLE_NAME for role in roles)
