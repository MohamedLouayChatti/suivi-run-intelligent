from __future__ import annotations

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.domain.entities.audit_entry import AuditEntry
from app.modules.audit.infrastructure.persistence.models.audit_entry_model import AuditEntryModel


def entry_to_model(entry: AuditEntry) -> AuditEntryModel:
	return AuditEntryModel(
		id=entry.id,
		occurred_at=entry.occurred_at,
		module=entry.module,
		event_type=entry.event_type,
		action=entry.action,
		resource_type=entry.resource_type,
		actor_id=entry.actor_id,
		payload=entry.payload,
	)


def model_to_dto(model: AuditEntryModel) -> AuditEntryDTO:
	return AuditEntryDTO(
		id=model.id,
		occurred_at=model.occurred_at,
		module=model.module,
		event_type=model.event_type,
		action=model.action,
		resource_type=model.resource_type,
		actor_id=model.actor_id,
		payload=model.payload,
	)
