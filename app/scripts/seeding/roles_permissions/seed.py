from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
from app.shared.database.engine import engine
from app.shared.database.session import create_session
from app.shared.seeding.roles_permissions.permissions import PERMISSION_CATALOG, PERMISSIONS_BY_NAME
from app.shared.seeding.roles_permissions.roles import SEEDED_ROLE_DEFINITIONS, SEEDED_ROLE_NAMES

logger = logging.getLogger(__name__)


async def synchronize_authorization_data(session: AsyncSession) -> None:
	"""Make permissions, seeded roles, and their assignments match the catalogs."""
	await _synchronize_permissions(session)
	await session.flush()
	await _synchronize_roles(session)
	await _remove_stale_roles(session)
	await session.flush()
	await _remove_stale_permissions(session)


async def _synchronize_permissions(session: AsyncSession) -> None:
	models = list((await session.scalars(select(PermissionModel))).all())
	by_name = {model.name: model for model in models}

	for definition in PERMISSION_CATALOG:
		model = by_name.get(definition.name)
		if model is None:
			model = PermissionModel(id=uuid4(), name=definition.name, description=definition.description)
			session.add(model)
			by_name[definition.name] = model
		elif model.description != definition.description:
			model.description = definition.description


async def _synchronize_roles(session: AsyncSession) -> None:
	permission_models = {
		model.name: model
		for model in (await session.scalars(select(PermissionModel))).all()
	}
	role_models = {
		model.name: model
		for model in (
			await session.scalars(select(RoleModel).options(selectinload(RoleModel.permissions)))
		).all()
	}

	for definition in SEEDED_ROLE_DEFINITIONS:
		role = role_models.get(definition.name)
		if role is None:
			role = RoleModel(id=uuid4(), name=definition.name)
			session.add(role)
			role_models[definition.name] = role
		role.permissions = _permissions_for_names(definition.permission_names, permission_models)


def _permissions_for_names(names: Iterable[str], permission_models: dict[str, PermissionModel]) -> list[PermissionModel]:
	try:
		return [permission_models[name] for name in names]
	except KeyError as error:
		raise ValueError(f"Role references unknown permission: {error.args[0]}") from error


async def _remove_stale_roles(session: AsyncSession) -> None:
	roles = list((await session.scalars(select(RoleModel))).all())
	for role in roles:
		if role.name not in SEEDED_ROLE_NAMES:
			await session.delete(role)


async def _remove_stale_permissions(session: AsyncSession) -> None:
	models = list((await session.scalars(select(PermissionModel))).all())
	current_names = set(PERMISSIONS_BY_NAME)
	for model in models:
		if model.name not in current_names:
			await session.delete(model)


async def seed_database() -> None:
	async with create_session() as session:
		try:
			async with session.begin():
				await synchronize_authorization_data(session)
		except Exception:
			logger.exception("Authorization reference-data seeding failed")
			raise
	logger.info("Authorization reference data synchronized")
	await engine.dispose()


def main() -> None:
	asyncio.run(seed_database())


if __name__ == "__main__":
	main()
