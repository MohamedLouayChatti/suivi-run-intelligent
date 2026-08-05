from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.modules.auth.application.commands.create_user.command import CreateUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.constants import DEFAULT_ROLE_NAME
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.events.user_created import UserCreated
from app.shared.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class CreateUserHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: CreateUserCommand) -> UserDTO:
		user = User.create(
			id=command.user_id,
			auth_provider_user_id=command.auth_provider_user_id,
			email=command.email,
			display_name=command.display_name,
			avatar_url=command.avatar_url,
			functional_team=command.functional_team,
			application_assignments=set(command.application_assignments),
		)

		default_role = await self.uow.roles.get_by_name(DEFAULT_ROLE_NAME)
		if default_role is None:
			logger.warning("Default role %r not found; created user %s with no role.", DEFAULT_ROLE_NAME, user.id)
		else:
			user.assign_role(default_role.id)

		await self.uow.users.add(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			UserCreated(
				user_id=user.id,
				auth_provider_user_id=user.auth_provider_user_id,
				email=user.email,
				display_name=user.display_name,
				functional_team=user.functional_team,
				application_assignments=frozenset(user.application_assignments),
				occurred_at=datetime.now(UTC),
				actor_id=command.actor_id,
			)
		)
		return UserDTO.from_user(user)
