from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.exceptions import (
    InvalidAssignedRole,
    PermissionAlreadyGranted,
    PermissionNotGranted,
    PermissionPrerequisiteNotSatisfied,
)
from app.modules.auth.domain.value_objects.permission_dependency_graph import PermissionDependencyGraph


class AuthorizationService:
    """Resolves permissions across the User and Role aggregate boundaries."""

    @staticmethod
    def combine_permissions(
        *,
        role_permission_ids: Iterable[UUID],
        direct_permission_ids: Iterable[UUID],
        revoked_permission_ids: Iterable[UUID],
        dependencies: PermissionDependencyGraph,
    ) -> set[UUID]:
        """The effective-permission rule itself: role perms union direct perms, minus revoked,
        then narrowed to the part of that set whose prerequisites are actually present.

        Deliberately expressed over bare id collections rather than aggregates so the read
        side can reuse it verbatim.  The read model loads the same three sets straight from
        the role and the association tables and would otherwise have to restate this rule in
        SQL -- leaving the project's single most important authorization rule with two
        independent implementations that could silently diverge.

        The closure is applied *here*, at the one place both paths pass through, rather than
        on each write.  Write-path rules keep each aggregate coherent as it is edited, but
        they cannot cover every way the stored data can drift out of coherence: revoking a
        permission from a role cannot reach the members holding a dependent one directly,
        and doing so would mean a Role write mutating every member's User aggregate.  Filtering
        at resolution makes the *effective* set coherent whatever the stored data says, which
        is the set every authorization decision is actually made against.  The consequence,
        deliberate: a permission can be stored and still not be effective.
        """
        granted = (set(role_permission_ids) | set(direct_permission_ids)) - set(revoked_permission_ids)
        return dependencies.satisfied_subset(granted)

    def resolve_permissions(
        self,
        user: User,
        assigned_role: Role,
        dependencies: PermissionDependencyGraph,
    ) -> set[UUID]:
        if assigned_role.id != user.role_id:
            raise InvalidAssignedRole()

        return self.combine_permissions(
            role_permission_ids=assigned_role.permission_ids,
            direct_permission_ids=user.direct_permission_ids,
            revoked_permission_ids=user.revoked_permission_ids,
            dependencies=dependencies,
        )

    def has_permission(
        self,
        user: User,
        permission_id: UUID,
        assigned_role: Role,
        dependencies: PermissionDependencyGraph,
    ) -> bool:
        return permission_id in self.resolve_permissions(user, assigned_role, dependencies)

    def ensure_direct_permission_may_be_granted(
        self,
        user: User,
        permission: Permission,
        assigned_role: Role,
        dependencies: PermissionDependencyGraph,
        permission_names: dict[UUID, str],
    ) -> None:
        held = self.resolve_permissions(user, assigned_role, dependencies)
        if permission.id in held:
            raise PermissionAlreadyGranted()
        self._ensure_prerequisites_met(permission, held, dependencies, permission_names)

    def ensure_direct_permission_may_be_revoked(
        self,
        user: User,
        permission_id: UUID,
        assigned_role: Role,
        dependencies: PermissionDependencyGraph,
    ) -> None:
        if not self.has_permission(user, permission_id, assigned_role, dependencies):
            raise PermissionNotGranted()

    def ensure_role_permission_may_be_granted(
        self,
        role: Role,
        permission: Permission,
        dependencies: PermissionDependencyGraph,
        permission_names: dict[UUID, str],
    ) -> None:
        """The role-side counterpart, checked against the role's own set.

        A role is validated against what it itself holds rather than against any member's
        effective permissions: a role is a bundle designed to stand on its own, and one that
        is only coherent for the members who happen to hold the missing piece directly is not
        a bundle anyone could reason about.
        """
        if permission.id in role.permission_ids:
            raise PermissionAlreadyGranted()
        self._ensure_prerequisites_met(permission, role.permission_ids, dependencies, permission_names)

    @staticmethod
    def cascade_for_revocation(
        permission_id: UUID,
        *,
        held: Iterable[UUID],
        dependencies: PermissionDependencyGraph,
    ) -> frozenset[UUID]:
        """Everything that must come away alongside `permission_id`, itself included.

        Revoking a permission others depend on leaves them held but unusable, which is the
        state this whole relation exists to prevent -- so the dependents come away in the same
        administrative act rather than lingering as stored-but-not-effective.
        """
        return frozenset({permission_id}) | dependencies.dependents_of(permission_id, within=held)

    @staticmethod
    def _ensure_prerequisites_met(
        permission: Permission,
        held: Iterable[UUID],
        dependencies: PermissionDependencyGraph,
        permission_names: dict[UUID, str],
    ) -> None:
        missing = dependencies.missing_prerequisites(permission.id, held=held)
        if missing:
            raise PermissionPrerequisiteNotSatisfied(
                permission.name,
                frozenset(permission_names.get(permission_id, str(permission_id)) for permission_id in missing),
            )
