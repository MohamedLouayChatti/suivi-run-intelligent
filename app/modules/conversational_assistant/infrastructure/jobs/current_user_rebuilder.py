from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.queries.get_effective_permissions.handler import GetEffectivePermissionsHandler
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_permission_read_repository import (
	SqlAlchemyPermissionReadRepository,
)
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.shared.security.current_user import CurrentUser


async def rebuild_current_user(user_id: UUID, session: AsyncSession) -> CurrentUser:
	"""Reconstructs a CurrentUser inside a background job, which has no request-scoped one to
	inject.

	Uses the same collaborators `get_current_user` itself uses, minus token verification -- that
	step is legitimate to skip here because the conversation's ownership was already authorized
	through `get_current_user` + `require_instance_permission("conversation", "append", ...)` at
	send-message time. This re-resolves *fresh* permissions for an already-authenticated,
	already-owned resource; it is not a new authentication bypass, and re-resolving rather than
	snapshotting means a permission change between send and run takes effect immediately.
	"""
	user_repository = SqlAlchemyUserReadRepository(session)
	permission_repository = SqlAlchemyPermissionReadRepository(session)
	user = await user_repository.get_user(user_id)
	permissions_handler = GetEffectivePermissionsHandler(permission_repository)
	effective = await permissions_handler.handle(GetEffectivePermissionsQuery(user_id=user.id))
	return CurrentUser(
		id=user.id,
		auth_provider_user_id=user.auth_provider_user_id.value,
		email=user.email,
		display_name=user.display_name,
		functional_team=user.functional_team,
		application_assignments=user.application_assignments,
		role_id=user.role_id,
		permissions=frozenset(permission.name for permission in effective),
	)
