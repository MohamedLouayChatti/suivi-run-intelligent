from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.entities.permission import Permission


@dataclass(frozen=True)
class PermissionDTO:
	id: UUID
	name: str
	description: str

	@classmethod
	def from_permission(cls, permission: Permission) -> PermissionDTO:
		return cls(id=permission.id, name=permission.name, description=permission.description)
