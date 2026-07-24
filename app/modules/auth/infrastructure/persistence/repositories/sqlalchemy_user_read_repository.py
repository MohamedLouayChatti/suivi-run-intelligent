from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
from app.modules.auth.infrastructure.persistence.models.user_model import UserModel


class SqlAlchemyUserReadRepository(UserReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_user(self, user_id: UUID) -> UserDTO | None:
		model = await self._load_user(user_id)
		return None if model is None else mapper.user_model_to_dto(model)

	async def get_user_by_auth_provider_user_id(
		self, auth_provider_user_id: str
	) -> UserDTO | None:
		model = await self.session.scalar(
			self._base_query().where(UserModel.auth_provider_user_id == auth_provider_user_id)
		)
		return None if model is None else mapper.user_model_to_dto(model)

	async def list_users(self, query: ListUsersQuery) -> list[UserDTO]:
		result = await self.session.scalars(self._base_query().order_by(UserModel.email).limit(query.limit).offset(query.offset))
		return [mapper.user_model_to_dto(model) for model in result.all()]

	async def get_user_roles(self, user_id: UUID) -> list[RoleDTO]:
		model = await self._load_user(user_id)
		return [] if model is None else [mapper.role_model_to_dto(role) for role in model.roles]

	async def get_user_direct_permissions(self, user_id: UUID) -> list[PermissionDTO]:
		model = await self._load_user(user_id)
		return [] if model is None else [mapper.permission_model_to_dto(permission) for permission in model.direct_permissions]

	async def get_user_revoked_permissions(self, user_id: UUID) -> list[PermissionDTO]:
		model = await self._load_user(user_id)
		return [] if model is None else [mapper.permission_model_to_dto(permission) for permission in model.revoked_permissions]

	def _base_query(self) -> Select[tuple[UserModel]]:
		return select(UserModel).options(
			selectinload(UserModel.roles).selectinload(RoleModel.permissions),
			selectinload(UserModel.direct_permissions),
			selectinload(UserModel.revoked_permissions),
			selectinload(UserModel.application_assignments),
		)

	async def _load_user(self, user_id: UUID) -> UserModel | None:
		return await self.session.scalar(self._base_query().where(UserModel.id == user_id))
