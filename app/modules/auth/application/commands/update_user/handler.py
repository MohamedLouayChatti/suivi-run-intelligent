from __future__ import annotations

from app.modules.auth.application.commands.update_user.command import UpdateUserCommand
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import UserNotFound
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork


class UpdateUserHandler:
	def __init__(self, uow: UnitOfWork) -> None:
		self.uow = uow

	async def handle(self, command: UpdateUserCommand) -> UserDTO:
		user = await self.uow.users.get_by_id(command.user_id)
		if user is None:
			raise UserNotFound()
		if command.email is not None:
			user.email = command.email
		if command.display_name is not None:
			user.display_name = command.display_name
		if command.avatar_url is not None:
			user.avatar_url = command.avatar_url
		if command.functional_team is not None or command.application_assignments is not None:
			user.update_organizational_identity(
				functional_team=command.functional_team,
				application_assignments=None if command.application_assignments is None else set(command.application_assignments),
			)
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		return UserDTO.from_user(user)
