from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.events.role_permission_granted import RolePermissionGranted
from app.modules.auth.domain.events.role_permission_revoked import RolePermissionRevoked
from app.shared.events.event import DomainEvent


@dataclass
class Role:
	"""Authorization aggregate that owns permissions granted to a role."""

	id: UUID
	name: str
	permission_ids: set[UUID] = field(default_factory=set)
	requires_primary_application: bool = False
	"""Whether nobody may hold this role without an application of their own to run.

	A declared property of the role, not a fact inferred from its name or from the permissions
	it happens to bundle.  Both alternatives were considered and neither survives contact with
	this codebase: nothing anywhere branches on a role name, and the Admin role is seeded with
	every permission, so any permission-derived reading of "is this a staffed role" catches
	administrators too -- who legitimately run no application.

	Declaring it here also means the frontend can ask a role whether it needs staffing instead
	of carrying its own copy of which roles those are.
	"""

	def grant_permission(self, permission_id: UUID) -> None:
		if permission_id in self.permission_ids:
			return
		self.permission_ids.add(permission_id)

	def revoke_permission(self, permission_id: UUID) -> None:
		if permission_id not in self.permission_ids:
			return
		self.permission_ids.remove(permission_id)
