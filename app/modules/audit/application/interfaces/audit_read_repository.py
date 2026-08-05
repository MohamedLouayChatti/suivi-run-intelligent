from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.application.queries.list_audit_entries.query import ListAuditEntriesQuery


class AuditReadRepository(ABC):
	@abstractmethod
	async def get_entry(self, entry_id: UUID) -> AuditEntryDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_entries(self, query: ListAuditEntriesQuery) -> list[AuditEntryDTO]:
		raise NotImplementedError
