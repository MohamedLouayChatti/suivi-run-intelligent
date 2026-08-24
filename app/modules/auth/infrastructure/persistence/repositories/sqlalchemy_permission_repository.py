from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.repositories.permission_repository import PermissionRepository
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.association_tables import permission_dependencies
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
		"""The whole catalog with its dependency edges, as two flat queries.

		Deliberately built from Core selects rather than by loading `PermissionModel`: every
		relationship on that model is `lazy="selectin"`, so mapping forty permissions through
		the ORM would pull in every role and every user twice over.  This is called on each
		permission grant and revoke to build the dependency graph, so it has to stay cheap.
		"""
		rows = (await self.session.execute(select(PermissionModel.id, PermissionModel.name, PermissionModel.description))).all()
		edges: dict[UUID, set[UUID]] = {}
		for permission_id, required_id in (await self.session.execute(select(permission_dependencies))).all():
			edges.setdefault(permission_id, set()).add(required_id)
		return [
			Permission(
				id=row.id,
				name=row.name,
				description=row.description,
				required_permission_ids=frozenset(edges.get(row.id, ())),
			)
			for row in rows
		]

	async def exists(self, permission_id: UUID) -> bool:
		return await self.session.scalar(select(PermissionModel.id).where(PermissionModel.id == permission_id)) is not None

	async def _load_permission_model(self, condition) -> PermissionModel | None:
		return await self.session.scalar(select(PermissionModel).where(condition))
