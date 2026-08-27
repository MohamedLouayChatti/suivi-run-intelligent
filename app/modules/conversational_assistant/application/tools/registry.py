from __future__ import annotations

from app.modules.conversational_assistant.application.tools.base import ToolSpec
from app.modules.conversational_assistant.application.tools.get_attention_required import GET_ATTENTION_REQUIRED
from app.modules.conversational_assistant.application.tools.get_distributions import GET_DISTRIBUTIONS
from app.modules.conversational_assistant.application.tools.get_engineer_activity import GET_ENGINEER_ACTIVITY
from app.modules.conversational_assistant.application.tools.get_jira_metrics import GET_JIRA_METRICS
from app.modules.conversational_assistant.application.tools.get_kpi_snapshot import GET_KPI_SNAPSHOT
from app.modules.conversational_assistant.application.tools.get_my_activity_trend import GET_MY_ACTIVITY_TREND
from app.modules.conversational_assistant.application.tools.get_my_kpi_snapshot import GET_MY_KPI_SNAPSHOT
from app.modules.conversational_assistant.application.tools.get_similar_incidents import GET_SIMILAR_INCIDENTS
from app.modules.conversational_assistant.application.tools.get_ticket_comments import GET_TICKET_COMMENTS
from app.modules.conversational_assistant.application.tools.get_ticket_detail import GET_TICKET_DETAIL
from app.modules.conversational_assistant.application.tools.lookup_engineer import LOOKUP_ENGINEER
from app.modules.conversational_assistant.application.tools.search_tickets import SEARCH_TICKETS
from app.shared.security.current_user import CurrentUser

# Grouped by what a question is *about* rather than by which module answers it: tickets, people,
# and the aggregate view. The people group is the one the v1 set was missing outright -- it could
# name an engineer but say nothing about their work, so every question about a colleague ended in
# an apology for data the application plainly holds.
ALL_TOOL_SPECS: tuple[ToolSpec, ...] = (
	# Tickets
	GET_TICKET_DETAIL,
	GET_TICKET_COMMENTS,
	SEARCH_TICKETS,
	GET_SIMILAR_INCIDENTS,
	# People
	LOOKUP_ENGINEER,
	GET_ENGINEER_ACTIVITY,
	GET_MY_KPI_SNAPSHOT,
	GET_MY_ACTIVITY_TREND,
	# Aggregate reporting
	GET_KPI_SNAPSHOT,
	GET_DISTRIBUTIONS,
	GET_ATTENTION_REQUIRED,
	GET_JIRA_METRICS,
)


def build_available_tools(current_user: CurrentUser) -> list[ToolSpec]:
	"""Tool-availability authorization (layer 1 of 2): a tool wrapping a handler this user's
	permissions can't satisfy is never bound into the graph for this run, so the LLM never even
	sees it as an option. Resource-level authorization (layer 2) still runs inside each tool's
	own `execute` on every call, exactly as if it had gone through the ordinary HTTP route.
	"""
	return [spec for spec in ALL_TOOL_SPECS if current_user.has_permission(spec.required_permission)]
