from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.application.dto.user_summary_dto import UserSummaryDTO


class AuditActorSummaryResponse(BaseModel):
	"""Distinct name from Ticket Management's UserSummaryResponse: same shape today, but
	FastAPI keys OpenAPI components by class __name__ — reusing that name here would make
	the two silently share one schema entry (harmless only as long as both stay identical)."""

	id: UUID
	display_name: str
	avatar_url: str | None

	@classmethod
	def from_dto(cls, user: UserSummaryDTO | None) -> AuditActorSummaryResponse | None:
		return None if user is None else cls(id=user.id, display_name=user.display_name, avatar_url=user.avatar_url)


class AuditEntryResponse(BaseModel):
	id: UUID
	occurred_at: datetime
	module: str
	event_type: str
	action: str
	resource_type: str | None
	actor_id: UUID | None
	actor: AuditActorSummaryResponse | None
	actor_label: str | None
	payload: dict[str, Any]

	@classmethod
	def from_dto(cls, entry: AuditEntryDTO) -> AuditEntryResponse:
		return cls(
			id=entry.id,
			occurred_at=entry.occurred_at,
			module=entry.module,
			event_type=entry.event_type,
			action=entry.action,
			resource_type=entry.resource_type,
			actor_id=entry.actor_id,
			actor=AuditActorSummaryResponse.from_dto(entry.actor),
			actor_label=entry.actor_label,
			payload=entry.payload,
		)
