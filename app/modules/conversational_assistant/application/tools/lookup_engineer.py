from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.auth.application.queries.list_users.handler import ListUsersHandler
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import name_match_rank, name_matches

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
		# Token-wise and accent-insensitive rather than substring containment: the directory
		# stores one name order and callers type either, so "Yassine Kraiem" has to reach
		# "Kraiem Yassine". Ranked so the closest match leads, since a partial surname can
		# legitimately answer for several people.
		matches = sorted(
			(user for user in users if name_matches(args.name, user.display_name)),
			key=lambda user: name_match_rank(args.name, user.display_name),
		)[:_MAX_RESULTS]

		if not matches:
			return ToolResult(
				ok=False,
				error=(
					f"Aucun ingénieur ne correspond à « {args.name} ». Essayez un nom partiel "
					"(nom de famille seul, par exemple)."
				),
			)

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
		"Recherche un ingénieur par nom et retourne son identifiant, son équipe fonctionnelle "
		"et ses affectations applicatives. Le nom peut être donné dans n'importe quel ordre "
		"(prénom d'abord ou nom d'abord), partiellement et sans accents. "
		"Utilisez l'identifiant retourné pour interroger son activité ou ses tickets."
	),
	args_model=LookupEngineerArgs,
	required_permission="user.read",
	execute=_execute,
)
