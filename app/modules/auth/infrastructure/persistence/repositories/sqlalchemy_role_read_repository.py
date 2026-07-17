from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.queries.list_roles.query import ListRolesQuery
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel


class SqlAlchemyRoleReadRepository(RoleReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_role(self, role_id: UUID) -> RoleDTO | None:
		model = await self.session.scalar(self._base_query().where(RoleModel.id == role_id))
		return None if model is None else mapper.role_model_to_dto(model)

	async def list_roles(self, query: ListRolesQuery) -> list[RoleDTO]:
		result = await self.session.scalars(self._base_query().order_by(RoleModel.name).limit(query.limit).offset(query.offset))
		return [mapper.role_model_to_dto(model) for model in result.all()]

	async def get_role_permissions(self, role_id: UUID) -> list[PermissionDTO]:
		model = await self.session.scalar(self._base_query().where(RoleModel.id == role_id))
		return [] if model is None else [mapper.permission_model_to_dto(permission) for permission in model.permissions]

	def _base_query(self) -> Select[tuple[RoleModel]]:
		return select(RoleModel).options(selectinload(RoleModel.permissions))
