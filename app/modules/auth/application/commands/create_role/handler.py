from __future__ import annotations

from app.modules.auth.application.commands.create_role.command import CreateRoleCommand
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.exceptions import RoleAlreadyExists
from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.domain.entities.role import Role


class CreateRoleHandler:
	def __init__(self, uow: UnitOfWork) -> None:
		self.uow = uow

	async def handle(self, command: CreateRoleCommand) -> RoleDTO:
		if await self.uow.roles.get_by_name(command.name) is not None:
			raise RoleAlreadyExists()
		role = Role(id=command.role_id, name=command.name)
		await self.uow.roles.add(role)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		return RoleDTO.from_role(role)
