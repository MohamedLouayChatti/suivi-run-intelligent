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

	@classmethod
	def from_dto(cls, role: RoleDTO) -> RoleResponse:
		return cls(id=role.id, name=role.name, permission_ids=role.permission_ids)
