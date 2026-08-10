from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.list_roles.query import ListRolesQuery
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository

TicketReadRepositoryScope = Callable[[], AbstractAsyncContextManager[TicketReadRepository]]
UserReadRepositoryScope = Callable[[], AbstractAsyncContextManager[UserReadRepository]]
RoleReadRepositoryScope = Callable[[], AbstractAsyncContextManager[RoleReadRepository]]
PermissionReadRepositoryScope = Callable[[], AbstractAsyncContextManager[PermissionReadRepository]]

ADMIN_ROLE_NAME = "Admin"
"""The only role name still referenced anywhere in the codebase -- and deliberately so.

This is an *audience*, not an authorization check: it answers "who should be told", never
"who is allowed". Authorization branches solely on permissions (see
`app/shared/security/permissions.py`); nothing here grants or denies access. Treating the
administrators as a notification audience is a routing decision that belongs to this module,
and resolving it by permission instead would mean granting a permission silently changed who
gets paged.
"""

# Large enough to cover this system's entire user base in one page -- an internal
# support tool, not a mass-user product. Deliberately avoids adding a new filtered
# query method to Auth's public interface just for this module's broadcast cases;
# see the plan's note on this tradeoff.
_BULK_PAGE_SIZE = 10_000


class RecipientResolver:
	"""Resolves "who should be notified" against Ticket Management's and Auth's own
	Application-layer read interfaces -- the same sanctioned cross-module path
	Ticket Management already uses to enrich reads with UserSummaryDTO, and Audit
	already uses via AuditUserEnricher."""

	def __init__(
		self,
		ticket_repository_scope: TicketReadRepositoryScope,
		user_repository_scope: UserReadRepositoryScope,
		role_repository_scope: RoleReadRepositoryScope,
		permission_repository_scope: PermissionReadRepositoryScope,
	) -> None:
		self._ticket_repository_scope = ticket_repository_scope
		self._user_repository_scope = user_repository_scope
		self._role_repository_scope = role_repository_scope
		self._permission_repository_scope = permission_repository_scope

	async def get_ticket(self, ticket_id: UUID) -> TicketDetailDTO | None:
		async with self._ticket_repository_scope() as tickets:
			return await tickets.get_ticket(ticket_id)

	async def get_role_name(self, role_id: UUID) -> str | None:
		async with self._role_repository_scope() as roles:
			role = await roles.get_role(role_id)
		return role.name if role is not None else None

	async def get_permission(self, permission_id: UUID) -> PermissionDTO | None:
		async with self._permission_repository_scope() as permissions:
			return await permissions.get_permission(permission_id)

	async def _all_active_users(self) -> list[UserDTO]:
		async with self._user_repository_scope() as users:
			return await users.list_users(ListUsersQuery(limit=_BULK_PAGE_SIZE, offset=0))

	async def active_user_ids_with_role(self, role_id: UUID) -> set[UUID]:
		users = await self._all_active_users()
		return {user.id for user in users if user.active and role_id in user.role_ids}

	async def active_admin_user_ids(self) -> set[UUID]:
		async with self._role_repository_scope() as roles:
			role_list = await roles.list_roles(ListRolesQuery(limit=_BULK_PAGE_SIZE, offset=0))
		admin_role = next((role for role in role_list if role.name == ADMIN_ROLE_NAME), None)
		if admin_role is None:
			return set()
		return await self.active_user_ids_with_role(admin_role.id)

	async def active_user_ids_with_application(self, application_value: str, functional_team_value: str | None = None) -> set[UUID]:
		"""functional_team_value narrows to users whose own functional_team matches --
		needed for destinations that split by team (Support vs Configuration FCI/COLORIS).
		Pass None for destinations with no such split (AERO, VIO), where any user
		assigned to the application is a valid recipient regardless of their team."""
		users = await self._all_active_users()
		return {
			user.id
			for user in users
			if user.active
			and any(assignment.application.value == application_value for assignment in user.application_assignments)
			and (functional_team_value is None or user.functional_team.value == functional_team_value)
		}
