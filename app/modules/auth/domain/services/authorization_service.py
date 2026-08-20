from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.exceptions import (
    InvalidAssignedRole,
    PermissionAlreadyGranted,
    PermissionNotGranted,
)


class AuthorizationService:
    """Resolves permissions across the User and Role aggregate boundaries."""

    @staticmethod
    def combine_permissions(
        *,
        role_permission_ids: Iterable[UUID],
        direct_permission_ids: Iterable[UUID],
        revoked_permission_ids: Iterable[UUID],
    ) -> set[UUID]:
        """The effective-permission rule itself: role perms union direct perms, minus revoked.

        Deliberately expressed over bare id collections rather than aggregates so the read
        side can reuse it verbatim.  The read model loads the same three sets straight from
        the role and the association tables and would otherwise have to restate this rule in
        SQL -- leaving the project's single most important authorization rule with two
        independent implementations that could silently diverge.
        """
        return (set(role_permission_ids) | set(direct_permission_ids)) - set(revoked_permission_ids)

    def resolve_permissions(
        self,
        user: User,
        assigned_role: Role,
    ) -> set[UUID]:
        if assigned_role.id != user.role_id:
            raise InvalidAssignedRole()

        return self.combine_permissions(
            role_permission_ids=assigned_role.permission_ids,
            direct_permission_ids=user.direct_permission_ids,
            revoked_permission_ids=user.revoked_permission_ids,
        )

    def has_permission(
        self,
        user: User,
        permission_id: UUID,
        assigned_role: Role,
    ) -> bool:
        return permission_id in self.resolve_permissions(user, assigned_role)

    def ensure_direct_permission_may_be_granted(
        self,
        user: User,
        permission_id: UUID,
        assigned_role: Role,
    ) -> None:
        
        if self.has_permission(user, permission_id, assigned_role):
            raise PermissionAlreadyGranted()

    def ensure_direct_permission_may_be_revoked(
        self,
        user: User,
        permission_id: UUID,
        assigned_role: Role,
    ) -> None:

        if not self.has_permission(user, permission_id, assigned_role):
            raise PermissionNotGranted()
