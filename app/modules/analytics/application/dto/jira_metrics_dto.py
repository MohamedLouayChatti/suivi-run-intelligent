from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JiraMetricsDTO:
	"""requires_jira/jira_id are always set together at ticket creation (see
	Ticket._validate_conditional_fields), so "has a Jira ID" can't distinguish a state --
	the only later-filled Jira signal is jira_delivery_date, which is what
	awaiting_delivery/avg_delivery_delay_days are built from."""

	requires_jira: int
	awaiting_delivery: int
	avg_delivery_delay_days: float
