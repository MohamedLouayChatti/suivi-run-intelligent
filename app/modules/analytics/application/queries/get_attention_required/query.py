from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.application import Application

# Business default inherited from the frontend's mock generator -- open incidents older
# than this are flagged as needing attention. Tunable, not currently configurable per app.
DEFAULT_ATTENTION_THRESHOLD_DAYS = 6


@dataclass(frozen=True)
class GetAttentionRequiredQuery:
	applications: frozenset[Application] | None = None
	threshold_days: int = DEFAULT_ATTENTION_THRESHOLD_DAYS
