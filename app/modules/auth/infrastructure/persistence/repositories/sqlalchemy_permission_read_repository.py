from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.modules.auth.application.queries.list_permissions.query import ListPermissionsQuery
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
from app.modules.auth.infrastructure.persistence.models.user_model import UserModel


class SqlAlchemyPermissionReadRepository(PermissionReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_permission(self, permission_id: UUID) -> PermissionDTO | None:
		model = await self.session.scalar(select(PermissionModel).where(PermissionModel.id == permission_id))
		return None if model is None else mapper.permission_model_to_dto(model)

	async def list_permissions(self, query: ListPermissionsQuery) -> list[PermissionDTO]:
		result = await self.session.scalars(select(PermissionModel).order_by(PermissionModel.name).limit(query.limit).offset(query.offset))
		return [mapper.permission_model_to_dto(model) for model in result.all()]

	async def get_effective_permissions(self, query: GetEffectivePermissionsQuery) -> list[PermissionDTO]:
		user = await self.session.scalar(
			select(UserModel).where(UserModel.id == query.user_id).options(
				selectinload(UserModel.roles).selectinload(RoleModel.permissions),
				selectinload(UserModel.direct_permissions),
				selectinload(UserModel.revoked_permissions),
			)
		)
		if user is None:
			return []
		role_permission_ids = {permission.id for role in user.roles for permission in role.permissions}
		permission_ids = (role_permission_ids | {permission.id for permission in user.direct_permissions}) - {permission.id for permission in user.revoked_permissions}
		if not permission_ids:
			return []
		result = await self.session.scalars(select(PermissionModel).where(PermissionModel.id.in_(permission_ids)).order_by(PermissionModel.name))
		return [mapper.permission_model_to_dto(model) for model in result.all()]
