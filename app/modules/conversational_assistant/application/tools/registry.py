from __future__ import annotations

from app.modules.conversational_assistant.application.tools.base import ToolSpec
from app.modules.conversational_assistant.application.tools.get_kpi_snapshot import GET_KPI_SNAPSHOT
from app.modules.conversational_assistant.application.tools.get_my_activity_trend import GET_MY_ACTIVITY_TREND
from app.modules.conversational_assistant.application.tools.get_my_kpi_snapshot import GET_MY_KPI_SNAPSHOT
from app.modules.conversational_assistant.application.tools.get_similar_incidents import GET_SIMILAR_INCIDENTS
from app.modules.conversational_assistant.application.tools.get_ticket_detail import GET_TICKET_DETAIL
from app.modules.conversational_assistant.application.tools.lookup_engineer import LOOKUP_ENGINEER
from app.modules.conversational_assistant.application.tools.search_tickets import SEARCH_TICKETS
from app.shared.security.current_user import CurrentUser

# A curated v1 set, not the whole application: one ticket lookup, one search, similar-incidents,
# two personal analytics tools, one team/application analytics tool, and an engineer lookup.
# Deliberately excludes raw comment threads, attachment access, Jira metrics, distributions and
# attention-required feeds -- addable later as more ToolSpecs with no change to the graph/loop.
ALL_TOOL_SPECS: tuple[ToolSpec, ...] = (
	GET_TICKET_DETAIL,
	SEARCH_TICKETS,
	GET_SIMILAR_INCIDENTS,
	GET_MY_KPI_SNAPSHOT,
	GET_MY_ACTIVITY_TREND,
	GET_KPI_SNAPSHOT,
	LOOKUP_ENGINEER,
)


def build_available_tools(current_user: CurrentUser) -> list[ToolSpec]:
	"""Tool-availability authorization (layer 1 of 2): a tool wrapping a handler this user's
	permissions can't satisfy is never bound into the graph for this run, so the LLM never even
	sees it as an option. Resource-level authorization (layer 2) still runs inside each tool's
	own `execute` on every call, exactly as if it had gone through the ordinary HTTP route.
	"""
	return [spec for spec in ALL_TOOL_SPECS if current_user.has_permission(spec.required_permission)]
