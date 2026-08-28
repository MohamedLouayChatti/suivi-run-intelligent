from __future__ import annotations

from app.modules.conversational_assistant.application.tools.base import ToolSpec
from app.modules.conversational_assistant.application.tools.get_activity_trend import GET_ACTIVITY_TREND
from app.modules.conversational_assistant.application.tools.get_admin_overview import GET_ADMIN_OVERVIEW
from app.modules.conversational_assistant.application.tools.get_application_insights import (
	GET_APPLICATION_INSIGHTS,
)
from app.modules.conversational_assistant.application.tools.get_attention_required import GET_ATTENTION_REQUIRED
from app.modules.conversational_assistant.application.tools.get_distributions import GET_DISTRIBUTIONS
from app.modules.conversational_assistant.application.tools.get_engineer_activity import GET_ENGINEER_ACTIVITY
from app.modules.conversational_assistant.application.tools.get_jira_metrics import GET_JIRA_METRICS
from app.modules.conversational_assistant.application.tools.get_kpi_snapshot import GET_KPI_SNAPSHOT
from app.modules.conversational_assistant.application.tools.get_my_activity_trend import GET_MY_ACTIVITY_TREND
from app.modules.conversational_assistant.application.tools.get_my_kpi_snapshot import GET_MY_KPI_SNAPSHOT
from app.modules.conversational_assistant.application.tools.get_resolution_ranking import GET_RESOLUTION_RANKING
from app.modules.conversational_assistant.application.tools.get_similar_incidents import GET_SIMILAR_INCIDENTS
from app.modules.conversational_assistant.application.tools.get_ticket_comments import GET_TICKET_COMMENTS
from app.modules.conversational_assistant.application.tools.get_ticket_detail import GET_TICKET_DETAIL
from app.modules.conversational_assistant.application.tools.list_engineers import LIST_ENGINEERS
from app.modules.conversational_assistant.application.tools.list_reference_values import LIST_REFERENCE_VALUES
from app.modules.conversational_assistant.application.tools.lookup_engineer import LOOKUP_ENGINEER
from app.modules.conversational_assistant.application.tools.search_tickets import SEARCH_TICKETS
from app.shared.security.current_user import CurrentUser

# Grouped by what a question is *about* rather than by which module answers it: tickets, people,
# the aggregate view, and the vocabulary the other three are addressed in.
#
# The reference group exists because of how the catalogue fails rather than what it covers: every
# filter here is a closed enum, and a model that cannot see the legal spellings guesses, gets
# refused, and burns its whole iteration budget guessing again. One tool that answers "what are
# the accepted values" turns that dead end into a single recovery call.
ALL_TOOL_SPECS: tuple[ToolSpec, ...] = (
	# Tickets
	GET_TICKET_DETAIL,
	GET_TICKET_COMMENTS,
	SEARCH_TICKETS,
	GET_SIMILAR_INCIDENTS,
	# People
	LOOKUP_ENGINEER,
	LIST_ENGINEERS,
	GET_ENGINEER_ACTIVITY,
	GET_MY_KPI_SNAPSHOT,
	GET_MY_ACTIVITY_TREND,
	# Aggregate reporting
	GET_KPI_SNAPSHOT,
	GET_DISTRIBUTIONS,
	GET_ACTIVITY_TREND,
	GET_ATTENTION_REQUIRED,
	GET_JIRA_METRICS,
	GET_RESOLUTION_RANKING,
	GET_APPLICATION_INSIGHTS,
	GET_ADMIN_OVERVIEW,
	# Reference data
	LIST_REFERENCE_VALUES,
)


def build_available_tools(current_user: CurrentUser) -> list[ToolSpec]:
	"""Tool-availability authorization (layer 1 of 2): a tool wrapping a handler this user's
	permissions can't satisfy is never bound into the graph for this run, so the LLM never even
	sees it as an option. Resource-level authorization (layer 2) still runs inside each tool's
	own `execute` on every call, exactly as if it had gone through the ordinary HTTP route.
	"""
	return [spec for spec in ALL_TOOL_SPECS if current_user.has_permission(spec.required_permission)]
