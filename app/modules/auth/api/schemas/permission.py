from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.auth.application.dto.permission_dto import PermissionDTO


class PermissionResponse(BaseModel):
	id: UUID
	name: str
	description: str

	@classmethod
	def from_dto(cls, permission: PermissionDTO) -> PermissionResponse:
		return cls(id=permission.id, name=permission.name, description=permission.description)
