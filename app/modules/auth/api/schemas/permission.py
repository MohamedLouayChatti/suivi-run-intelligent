from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.modules.auth.application.dto.permission_dto import PermissionDTO


class PermissionResponse(BaseModel):
	id: UUID
	name: str
	description: str
	required_permission_ids: list[UUID]
	"""The permissions this one cannot be used without -- direct prerequisites only.

	Published so the frontend can disable a permission whose prerequisites the target does
	not hold, and warn about what a revocation will take with it, without carrying its own
	copy of the relation -- the same reason `Role.requires_primary_application` is exposed.
	"""

	@classmethod
	def from_dto(cls, permission: PermissionDTO) -> PermissionResponse:
		return cls(
			id=permission.id,
			name=permission.name,
			description=permission.description,
			required_permission_ids=sorted(permission.required_permission_ids),
		)
