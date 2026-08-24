from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.modules.auth.application.queries.list_permissions.query import ListPermissionsQuery
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.modules.auth.domain.value_objects.permission_dependency_graph import PermissionDependencyGraph
from app.modules.auth.infrastructure.persistence import mapper
from app.modules.auth.infrastructure.persistence.models.association_tables import permission_dependencies
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
				selectinload(UserModel.role).selectinload(RoleModel.permissions),
				selectinload(UserModel.direct_permissions),
				selectinload(UserModel.revoked_permissions),
			)
		)
		if user is None:
			return []
		permission_ids = AuthorizationService.combine_permissions(
			role_permission_ids=(permission.id for permission in user.role.permissions),
			direct_permission_ids=(permission.id for permission in user.direct_permissions),
			revoked_permission_ids=(permission.id for permission in user.revoked_permissions),
			dependencies=await self._dependency_graph(),
		)
		if not permission_ids:
			return []
		result = await self.session.scalars(select(PermissionModel).where(PermissionModel.id.in_(permission_ids)).order_by(PermissionModel.name))
		return [mapper.permission_model_to_dto(model) for model in result.all()]

	async def _dependency_graph(self) -> PermissionDependencyGraph:
		"""The whole catalog's dependency edges, as one flat query.

		Read from the edge table directly rather than off the permissions already loaded above:
		`satisfied_subset` treats a permission it has no entry for as having no prerequisites,
		so a graph built from whichever rows a particular user happened to hold would quietly
		wave through exactly the permissions it is meant to filter out.
		"""
		edges: dict[UUID, frozenset[UUID]] = {}
		accumulator: dict[UUID, set[UUID]] = {}
		for permission_id, required_id in (await self.session.execute(select(permission_dependencies))).all():
			accumulator.setdefault(permission_id, set()).add(required_id)
		edges = {key: frozenset(value) for key, value in accumulator.items()}
		return PermissionDependencyGraph(edges)
