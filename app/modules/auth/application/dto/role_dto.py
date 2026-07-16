from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.entities.role import Role


@dataclass(frozen=True)
class RoleDTO:
	id: UUID
	name: str
	permission_ids: set[UUID] = field(default_factory=set)

	@classmethod
	def from_role(cls, role: Role) -> RoleDTO:
		return cls(id=role.id, name=role.name, permission_ids=set(role.permission_ids))
