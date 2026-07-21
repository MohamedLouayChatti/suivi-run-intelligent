from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.application.dto.user_dto import UserDTO


class UserCreateRequest(BaseModel):
	auth_provider_user_id: str = Field(min_length=1)
	email: str = Field(min_length=1)
	display_name: str = Field(min_length=1)


class UserUpdateRequest(BaseModel):
	email: str | None = Field(default=None, min_length=1)
	display_name: str | None = Field(default=None, min_length=1)


class UserResponse(BaseModel):
	id: UUID
	auth_provider_user_id: str
	email: str
	display_name: str
	active: bool
	role_ids: set[UUID]
	direct_permission_ids: set[UUID]
	revoked_permission_ids: set[UUID]

	@classmethod
	def from_dto(cls, user: UserDTO) -> UserResponse:
		return cls(
			id=user.id,
			auth_provider_user_id=user.auth_provider_user_id.value,
			email=user.email,
			display_name=user.display_name,
			active=user.active,
			role_ids=user.role_ids,
			direct_permission_ids=user.direct_permission_ids,
			revoked_permission_ids=user.revoked_permission_ids,
		)
