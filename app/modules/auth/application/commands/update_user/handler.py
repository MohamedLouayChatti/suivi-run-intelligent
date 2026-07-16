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
		await self.uow.users.update(user)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		return UserDTO.from_user(user)
