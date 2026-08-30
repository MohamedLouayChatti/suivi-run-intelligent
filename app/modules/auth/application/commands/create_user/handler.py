from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.modules.auth.application.commands.create_user.command import CreateUserCommand
from app.modules.auth.application.commands.create_user.organizational_identity import (
	DEFAULT_FUNCTIONAL_TEAM,
	parse_declared_organizational_identity,
)
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import DefaultRoleNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.constants import DEFAULT_ROLE_NAME
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.exceptions import FunctionalTeamNotAllowedForApplication
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.shared.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class CreateUserHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: CreateUserCommand) -> UserDTO:
		default_role = await self.uow.roles.get_by_name(DEFAULT_ROLE_NAME)
		if default_role is None:
			raise DefaultRoleNotFound()

		user = self._build_user(command, default_role.id)

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

	def _build_user(self, command: CreateUserCommand, role_id: UUID) -> User:
		"""Build the aggregate, dropping a self-declared identity it refuses.

		Only the applicant vouches for the pair they declared, so it can name a team that
		does not staff that application.  Attempted rather than pre-checked: the rule is the
		aggregate's, and asking it beforehand would mean writing it out a second time here.

		Dropping the declaration rather than failing on it is the deliberate part.  A user is
		only ever created from the identity provider's webhook, which fires *after* that
		provider has already stored the account, and nothing this handler answers can undo it
		there.  Refusing would leave a person who can authenticate against a system that
		cannot find them, with no second path to create the missing record.  So the account
		is always created, and an administrator corrects the assignment afterwards.
		"""
		functional_team, application_assignments = parse_declared_organizational_identity(
			command.declared_application, command.declared_functional_team
		)
		try:
			return self._new_user(command, role_id, functional_team, application_assignments)
		except FunctionalTeamNotAllowedForApplication:
			logger.warning(
				"Discarding the signup declaration for user %s: team %s does not staff %s.",
				command.user_id, functional_team.value, command.declared_application,
			)
			return self._new_user(command, role_id, DEFAULT_FUNCTIONAL_TEAM, frozenset())

	@staticmethod
	def _new_user(
		command: CreateUserCommand,
		role_id: UUID,
		functional_team: FunctionalTeam,
		application_assignments: frozenset[ApplicationAssignment],
	) -> User:
		return User.create(
			id=command.user_id,
			auth_provider_user_id=command.auth_provider_user_id,
			email=command.email,
			first_name=command.first_name,
			last_name=command.last_name,
			role_id=role_id,
			avatar_url=command.avatar_url,
			functional_team=functional_team,
			application_assignments=set(application_assignments),
		)
