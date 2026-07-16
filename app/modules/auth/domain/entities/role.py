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

	def grant_permission(self, permission_id: UUID) -> None:
		if permission_id in self.permission_ids:
			return
		self.permission_ids.add(permission_id)

	def revoke_permission(self, permission_id: UUID) -> None:
		if permission_id not in self.permission_ids:
			return
		self.permission_ids.remove(permission_id)
