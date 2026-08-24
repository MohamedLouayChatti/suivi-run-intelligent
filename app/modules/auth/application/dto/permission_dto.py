from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.entities.permission import Permission


@dataclass(frozen=True)
class PermissionDTO:
	id: UUID
	name: str
	description: str
	required_permission_ids: frozenset[UUID] = field(default_factory=frozenset)

	@classmethod
	def from_permission(cls, permission: Permission) -> PermissionDTO:
		return cls(
			id=permission.id,
			name=permission.name,
			description=permission.description,
			required_permission_ids=permission.required_permission_ids,
		)
