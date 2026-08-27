from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.auth.application.queries.list_users.handler import ListUsersHandler
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec

# One page is enough to cover this application's whole user base (including seeded historical
# users) without paging -- the directory this mirrors, GET /users/directory, has no pagination
# control on the frontend either.
_DIRECTORY_PAGE_SIZE = 500
_MAX_RESULTS = 5


class LookupEngineerArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	name: str


async def _execute(args: LookupEngineerArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		handler = ListUsersHandler(SqlAlchemyUserReadRepository(session))
		users = await handler.handle(ListUsersQuery(limit=_DIRECTORY_PAGE_SIZE, offset=0))
		needle = args.name.strip().casefold()
		matches = [user for user in users if needle in user.display_name.casefold()][:_MAX_RESULTS]
		return ToolResult(
			ok=True,
			# Same low-exposure shape as UserDirectoryResponse: id/display_name/active/team/
			# assignments only -- never email or role/permission ids, gated only by user.read
			# (held by every seeded role) for exactly that reason.
			payload={
				"engineers": [
					{
						"id": str(user.id),
						"display_name": user.display_name,
						"active": user.active,
						"functional_team": user.functional_team.value,
						"applications": [
							{
								"application": assignment.application.value,
								"assignment_type": assignment.assignment_type.value,
							}
							for assignment in user.application_assignments
						],
					}
					for user in matches
				]
			},
		)
	finally:
		await session.close()


LOOKUP_ENGINEER = ToolSpec(
	name="lookup_engineer",
	description=(
		"Recherche un ingénieur par nom (recherche partielle, insensible à la casse) et retourne "
		"son équipe fonctionnelle et ses affectations applicatives."
	),
	args_model=LookupEngineerArgs,
	required_permission="user.read",
	execute=_execute,
)
