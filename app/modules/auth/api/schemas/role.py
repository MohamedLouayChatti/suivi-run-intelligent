from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.application.dto.role_dto import RoleDTO


class RoleCreateRequest(BaseModel):
	name: str = Field(min_length=1)


class RoleResponse(BaseModel):
	id: UUID
	name: str
	permission_ids: set[UUID]
	requires_primary_application: bool
	"""Whether this role may only be held by someone who runs an application of their own.

	Exposed so a client can ask the role rather than carrying its own list of which roles those
	are -- the same reason the flag is declared on the Role instead of inferred from its name.
	"""

	@classmethod
	def from_dto(cls, role: RoleDTO) -> RoleResponse:
		return cls(
			id=role.id,
			name=role.name,
			permission_ids=role.permission_ids,
			requires_primary_application=role.requires_primary_application,
		)
