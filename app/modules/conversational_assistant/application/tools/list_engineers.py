from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.auth.application.queries.list_users.handler import ListUsersHandler
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam

# One page covers this application's whole user base, seeded historical users included -- the same
# assumption lookup_engineer makes, and the same one GET /users/directory makes by offering no
# pagination control at all.
_DIRECTORY_PAGE_SIZE = 500


class ListEngineersArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	functional_team: FunctionalTeam | None = None
	# Historical users are seeded inactive so imported tickets have valid assignees to point at,
	# so they outnumber the real team and would drown any question about who works here now.
	# Answering "who is on my team" with the active ones is the useful default; past activity is
	# still reachable by asking for everyone.
	active_only: bool = True


async def _execute(args: ListEngineersArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		handler = ListUsersHandler(SqlAlchemyUserReadRepository(session))
		users = await handler.handle(ListUsersQuery(limit=_DIRECTORY_PAGE_SIZE, offset=0))

		# Filtered here rather than in a new Auth query: the directory is one small page either
		# way, and the two axes wanted -- application and functional team -- are Auth's own value
		# objects, which this module may read through the DTO but must not teach Auth to index by
		# on its behalf.
		def matches(user) -> bool:
			if args.active_only and not user.active:
				return False
			if args.functional_team is not None and user.functional_team.value != args.functional_team.value:
				return False
			if args.application is not None and not any(
				assignment.application.value == args.application.value
				for assignment in user.application_assignments
			):
				return False
			return True

		matched = sorted((user for user in users if matches(user)), key=lambda user: user.display_name)
		return ToolResult(
			ok=True,
			payload={
				"count": len(matched),
				# Same low-exposure projection as lookup_engineer and GET /users/directory:
				# id/display_name/active/team/assignments, never email or role and permission ids.
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
					for user in matched
				],
			},
		)
	finally:
		await session.close()


LIST_ENGINEERS = ToolSpec(
	name="list_engineers",
	description=(
		"Liste les ingénieurs de l'organisation, avec leur identifiant, leur équipe "
		"fonctionnelle et leurs affectations applicatives. Filtrable par deux axes indépendants : "
		"application (FCI, COLORIS, AERO, VIO -- \"l'équipe FCI\", \"les ingénieurs COLORIS\") et "
		"équipe fonctionnelle (SUPPORT/\"SN3\" ou CONFIGURATION/\"Paramétrage\" -- un type de "
		"travail, jamais le nom d'une application). Utilisez cet outil quand la question porte sur "
		"une équipe ou sur l'ensemble des ingénieurs plutôt que sur une personne nommée : il donne "
		"les identifiants nécessaires pour interroger ensuite l'activité de chacun."
	),
	args_model=ListEngineersArgs,
	required_permission="user.read",
	execute=_execute,
)
