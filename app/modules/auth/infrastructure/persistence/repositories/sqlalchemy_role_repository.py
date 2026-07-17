from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.repositories.role_repository import RoleRepository
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel


class SqlAlchemyRoleRepository(RoleRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, role: Role) -> None:
		permissions = await self._load_permissions(role)
		self.session.add(mapper.role_to_model(role, permissions=permissions))

	async def get_by_id(self, role_id: UUID) -> Role | None:
		model = await self._load_role_model(RoleModel.id == role_id)
		return None if model is None else mapper.role_model_to_domain(model)

	async def get_by_name(self, name: str) -> Role | None:
		model = await self._load_role_model(RoleModel.name == name)
		return None if model is None else mapper.role_model_to_domain(model)

	async def update(self, role: Role) -> None:
		model = await self._load_role_model(RoleModel.id == role.id)
		if model is None:
			self.session.add(mapper.role_to_model(role, permissions=await self._load_permissions(role)))
			return
		mapper.sync_role_model(model, role, permissions=await self._load_permissions(role))

	async def list(self) -> list[Role]:
		result = await self.session.scalars(select(RoleModel).options(selectinload(RoleModel.permissions)))
		return [mapper.role_model_to_domain(model) for model in result.all()]

	async def _load_role_model(self, condition) -> RoleModel | None:
		return await self.session.scalar(select(RoleModel).where(condition).options(selectinload(RoleModel.permissions)))

	async def _load_permissions(self, role: Role) -> list[PermissionModel]:
		if not role.permission_ids:
			return []
		result = await self.session.scalars(select(PermissionModel).where(PermissionModel.id.in_(role.permission_ids)))
		return list(result.all())
