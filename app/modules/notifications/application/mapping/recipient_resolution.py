from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository

TicketReadRepositoryScope = Callable[[], AbstractAsyncContextManager[TicketReadRepository]]
UserReadRepositoryScope = Callable[[], AbstractAsyncContextManager[UserReadRepository]]
RoleReadRepositoryScope = Callable[[], AbstractAsyncContextManager[RoleReadRepository]]
PermissionReadRepositoryScope = Callable[[], AbstractAsyncContextManager[PermissionReadRepository]]

# Large enough to cover this system's entire user base in one page -- an internal
# support tool, not a mass-user product. It is what the two membership-shaped audiences
# below (a role's members, an application's staff) are resolved through, rather than
# adding a filtered query to Auth's public interface for each of them. The
# permission-shaped audience is the one exception: "who holds this permission" is set
# arithmetic over three tables, which is a query rather than a filter over a page.
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
		return {user.id for user in users if user.active and user.role_id == role_id}

	async def active_user_ids_with_permission(self, permission_name: str) -> set[UUID]:
		"""Everyone who holds `permission_name`, and is therefore this notification's audience.

		This replaced a lookup that resolved the role literally named "Admin" and broadcast to its
		members -- the last place in the codebase that read a role name as though it meant
		something. It was defended at the time as routing rather than authorization, on the
		grounds that "who should be told" is a different question from "who is allowed". It is
		not a different enough one: every broadcast that went through it was aimed at the people
		who could act on what it announced, and a role is only ever a bundle of the permissions
		that let them. Naming the permission directly is both the accurate audience and the one
		that follows a delegation -- granting `knowledge_base.read_recalculation` to another role,
		or to one person, now moves the notifications with it, which is exactly what granting it
		was meant to mean.

		Note this widens several audiences rather than merely re-expressing them: Chef de projet
		holds all three `knowledge_base.*` permissions, so the maintenance notices reach project
		managers as well as administrators. That is the rule working, not a side effect of it.
		"""
		async with self._user_repository_scope() as users:
			return await users.find_active_user_ids_with_permission(permission_name)

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
