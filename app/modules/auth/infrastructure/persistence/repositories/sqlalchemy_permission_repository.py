from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.repositories.permission_repository import PermissionRepository
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel


class SqlAlchemyPermissionRepository(PermissionRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_by_id(self, permission_id: UUID) -> Permission | None:
		model = await self._load_permission_model(PermissionModel.id == permission_id)
		return None if model is None else mapper.permission_model_to_domain(model)

	async def get_by_name(self, name: str) -> Permission | None:
		model = await self._load_permission_model(PermissionModel.name == name)
		return None if model is None else mapper.permission_model_to_domain(model)

	async def list(self) -> list[Permission]:
		result = await self.session.scalars(select(PermissionModel).options(selectinload(PermissionModel.roles)))
		return [mapper.permission_model_to_domain(model) for model in result.all()]

	async def exists(self, permission_id: UUID) -> bool:
		return await self.session.scalar(select(PermissionModel.id).where(PermissionModel.id == permission_id)) is not None

	async def _load_permission_model(self, condition) -> PermissionModel | None:
		return await self.session.scalar(select(PermissionModel).where(condition))
