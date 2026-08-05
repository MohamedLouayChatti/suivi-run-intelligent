from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.modules.audit.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.audit.domain.entities.audit_entry import AuditEntry


@dataclass(frozen=True)
class AuditEntryDTO:
	id: UUID
	occurred_at: datetime
	module: str
	event_type: str
	action: str
	resource_type: str | None
	actor_id: UUID | None
	payload: dict[str, Any] = field(default_factory=dict)
	actor: UserSummaryDTO | None = None

	@property
	def actor_label(self) -> str | None:
		"""Fallback description for entries with no internal actor_id at all.

		Every event type threads a real actor_id through except the two Clerk
		webhook-triggered auth events (UserCreated, UserUpdated), which have no
		authenticated CurrentUser to attribute. A null actor_id therefore always
		means "no authenticated staff action" rather than "unknown" -- this makes
		that fact explicit instead of leaving the client to guess or hardcode
		per-event-type knowledge of its own.
		"""
		return None if self.actor_id is not None else "System / identity provider (no authenticated user)"

	@classmethod
	def from_entry(cls, entry: AuditEntry) -> AuditEntryDTO:
		return cls(
			entry.id, entry.occurred_at, entry.module, entry.event_type,
			entry.action, entry.resource_type, entry.actor_id, entry.payload,
		)
