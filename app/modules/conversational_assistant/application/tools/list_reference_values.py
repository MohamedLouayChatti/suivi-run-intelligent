from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status

# Read off the enums themselves, never transcribed: a hand-written copy of a list like Category is
# a second source of truth that goes stale the first time somebody adds a member.
_VOCABULARY: dict[str, type] = {
	"application": Application,
	"status": Status,
	"priority": Priority,
	"category": Category,
	"functional_team": FunctionalTeam,
	"time_range": TimeRange,
}

_GLOSSES: dict[str, str] = {
	"application": (
		"Les applications suivies (FCI, COLORIS, AERO, VIO) -- l'axe \"qui travaille sur quoi\". "
		"Une phrase comme \"l'équipe FCI\" ou \"les gens de COLORIS\" filtre sur application, pas "
		"sur functional_team : il n'existe pas d'équipe fonctionnelle nommée FCI, COLORIS, AERO ou "
		"VIO."
	),
	"status": "Les statuts du cycle de vie d'un ticket.",
	"priority": "P1 est la plus urgente, P4 la moins urgente.",
	"category": "La nature de l'incident.",
	"functional_team": (
		"L'équipe fonctionnelle (SUPPORT, affiché \"SN3\" ; CONFIGURATION, affiché "
		"\"Paramétrage\") -- l'axe \"quel type de travail\", indépendant de l'application. AERO et "
		"VIO n'ont que des ingénieurs SUPPORT."
	),
	"time_range": "Les périodes d'analyse : 30 jours, 3 mois, 6 mois, 1 an.",
}


class ListReferenceValuesArgs(BaseModel):
	"""No fields: the whole vocabulary is small enough to return at once, and a filter would
	only give the model one more thing to get wrong at the exact moment it is asking because it
	got something wrong."""

	model_config = ConfigDict(extra="forbid")


async def _execute(args: ListReferenceValuesArgs, ctx: ToolContext) -> ToolResult:
	return ToolResult(
		ok=True,
		payload={
			name: {
				"valeurs": [member.value for member in enum],
				"description": _GLOSSES[name],
			}
			for name, enum in _VOCABULARY.items()
		},
	)


LIST_REFERENCE_VALUES = ToolSpec(
	name="list_reference_values",
	description=(
		"Retourne les valeurs exactes acceptées par les autres outils pour les paramètres "
		"application, statut, priorité, catégorie, équipe fonctionnelle et période d'analyse. "
		"Appelez cet outil si un appel a été refusé pour cause de valeur invalide, ou si "
		"l'utilisateur emploie un terme dont vous ignorez la valeur correspondante."
	),
	args_model=ListReferenceValuesArgs,
	# Every authenticated user holds ticket.read, and this returns no application data at all --
	# only the spelling of the filters. Gating it any harder would withhold the recovery path from
	# precisely the callers whose narrower tool set makes a wrong guess likelier.
	required_permission="ticket.read",
	execute=_execute,
)
