from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.enums.assignment_type import AssignmentType
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.engine import engine
from app.shared.seeding.users.historical_users import HISTORICAL_USERS, HistoricalUserDefinition

logger = logging.getLogger(__name__)


async def seed_historical_users(uow: SqlAlchemyUnitOfWork) -> None:
	"""Create the fake, inactive users referenced by imported historical tickets."""
	for definition in HISTORICAL_USERS:
		await _seed_user(uow, definition)


async def _seed_user(uow: SqlAlchemyUnitOfWork, definition: HistoricalUserDefinition) -> None:
	if await uow.users.get_by_email(definition.email) is not None:
		return

	role = await uow.roles.get_by_name(definition.role_name)
	if role is None:
		raise ValueError(f"Historical user references unknown role: {definition.role_name}")

	application_assignments = {
		ApplicationAssignment(application=definition.primary_application, assignment_type=AssignmentType.PRIMARY)
	}
	if definition.backup_application is not None:
		application_assignments.add(
			ApplicationAssignment(application=definition.backup_application, assignment_type=AssignmentType.BACKUP)
		)

	user = User.create(
		id=uuid4(),
		auth_provider_user_id=AuthProviderUserId(str(uuid4())),
		email=definition.email,
		display_name=definition.display_name,
		functional_team=definition.functional_team,
		application_assignments=application_assignments,
	)
	user.deactivate()
	user.assign_role(role.id)

	await uow.users.add(user)


async def seed_database() -> None:
	async with SqlAlchemyUnitOfWork() as uow:
		try:
			await seed_historical_users(uow)
			await uow.commit()
		except Exception:
			logger.exception("Historical user seeding failed")
			raise
	logger.info("Historical users synchronized")
	await engine.dispose()


def main() -> None:
	asyncio.run(seed_database())


if __name__ == "__main__":
	main()
