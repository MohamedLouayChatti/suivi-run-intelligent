from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, except_, func, select, union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.association_tables import (
	role_permissions,
	user_direct_permissions,
	user_revoked_permissions,
)
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
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

	async def find_by_display_names(self, display_names: Sequence[str]) -> list[UserDTO]:
		if not display_names:
			return []
		normalized = {name.strip().lower() for name in display_names}
		result = await self.session.scalars(
			self._base_query().where(func.lower(func.btrim(UserModel.display_name)).in_(normalized))
		)
		return [mapper.user_model_to_dto(model) for model in result.all()]

	async def find_active_user_ids_with_permission(self, permission_name: str) -> set[UUID]:
		# The set arithmetic is AuthorizationService's -- role permissions, plus direct grants,
		# minus revocations -- expressed in SQL rather than by calling it. That service decides
		# for one user from entities already in hand, and this question is asked of every user at
		# once: satisfying it through the service would mean loading every active user with their
		# role, grants and revocations just to intersect three id sets in Python. The rule is one
		# union and one difference, and the database states both exactly.
		permission_id = select(PermissionModel.id).where(PermissionModel.name == permission_name).scalar_subquery()

		# An unresolvable name makes this subquery NULL, so every comparison below is NULL and all
		# three branches come back empty -- which is the documented answer for a permission nobody
		# holds, reached without a separate existence check.
		through_role = (
			select(UserModel.id)
			.join(role_permissions, role_permissions.c.role_id == UserModel.role_id)
			.where(UserModel.active.is_(True), role_permissions.c.permission_id == permission_id)
		)
		granted_directly = (
			select(UserModel.id)
			.join(user_direct_permissions, user_direct_permissions.c.user_id == UserModel.id)
			.where(UserModel.active.is_(True), user_direct_permissions.c.permission_id == permission_id)
		)
		# Not filtered on `active`: this only ever subtracts, so rows for inactive users can never
		# add a recipient, and an extra predicate here would only be a second place to get wrong.
		revoked = select(user_revoked_permissions.c.user_id).where(
			user_revoked_permissions.c.permission_id == permission_id
		)

		result = await self.session.execute(except_(union(through_role, granted_directly), revoked))
		return {row[0] for row in result}

	async def get_user_role(self, user_id: UUID) -> RoleDTO | None:
		model = await self._load_user(user_id)
		return None if model is None else mapper.role_model_to_dto(model.role)

	async def get_user_direct_permissions(self, user_id: UUID) -> list[PermissionDTO]:
		model = await self._load_user(user_id)
		return [] if model is None else [mapper.permission_model_to_dto(permission) for permission in model.direct_permissions]

	async def get_user_revoked_permissions(self, user_id: UUID) -> list[PermissionDTO]:
		model = await self._load_user(user_id)
		return [] if model is None else [mapper.permission_model_to_dto(permission) for permission in model.revoked_permissions]

	def _base_query(self) -> Select[tuple[UserModel]]:
		return select(UserModel).options(
			selectinload(UserModel.role).selectinload(RoleModel.permissions),
			selectinload(UserModel.direct_permissions),
			selectinload(UserModel.revoked_permissions),
			selectinload(UserModel.application_assignments),
		)

	async def _load_user(self, user_id: UUID) -> UserModel | None:
		return await self.session.scalar(self._base_query().where(UserModel.id == user_id))
