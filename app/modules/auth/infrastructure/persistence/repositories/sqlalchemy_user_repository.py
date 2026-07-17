from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.user_repository import UserRepository
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
from app.modules.auth.infrastructure.persistence.models.user_model import UserModel


class SqlAlchemyUserRepository(UserRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, user: User) -> None:
		roles, permissions = await self._load_related(user)
		self.session.add(mapper.user_to_model(user, roles=roles, permissions=permissions))

	async def get_by_id(self, user_id: UUID) -> User | None:
		model = await self._load_user_model(UserModel.id == user_id)
		return None if model is None else mapper.user_model_to_domain(model)

	async def get_by_auth_provider_user_id(self, auth_provider_user_id: AuthProviderUserId) -> User | None:
		model = await self._load_user_model(UserModel.auth_provider_user_id == auth_provider_user_id.value)
		return None if model is None else mapper.user_model_to_domain(model)

	async def get_by_email(self, email: str) -> User | None:
		model = await self._load_user_model(UserModel.email == email)
		return None if model is None else mapper.user_model_to_domain(model)

	async def update(self, user: User) -> None:
		model = await self._load_user_model(UserModel.id == user.id)
		if model is None:
			self.session.add(await self._new_user_model(user))
			return
		roles, permissions = await self._load_related(user)
		mapper.sync_user_model(model, user, roles=roles, permissions=permissions)

	async def exists(self, user_id: UUID) -> bool:
		return await self.session.scalar(select(UserModel.id).where(UserModel.id == user_id)) is not None

	async def _load_user_model(self, condition) -> UserModel | None:
		stmt = select(UserModel).where(condition).options(
			selectinload(UserModel.roles), selectinload(UserModel.direct_permissions), selectinload(UserModel.revoked_permissions)
		)
		return await self.session.scalar(stmt)

	async def _load_related(self, user: User) -> tuple[list[RoleModel], list[PermissionModel]]:
		role_ids = list(user.role_ids)
		permission_ids = list(user.direct_permission_ids | user.revoked_permission_ids)
		roles = list((await self.session.scalars(select(RoleModel).where(RoleModel.id.in_(role_ids)))).all()) if role_ids else []
		permissions = list((await self.session.scalars(select(PermissionModel).where(PermissionModel.id.in_(permission_ids)))).all()) if permission_ids else []
		return roles, permissions

	async def _new_user_model(self, user: User) -> UserModel:
		roles, permissions = await self._load_related(user)
		return mapper.user_to_model(user, roles=roles, permissions=permissions)
