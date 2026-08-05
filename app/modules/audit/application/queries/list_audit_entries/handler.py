from __future__ import annotations

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.application.interfaces.audit_read_repository import AuditReadRepository
from app.modules.audit.application.queries.list_audit_entries.query import ListAuditEntriesQuery
from app.modules.audit.application.queries.user_enricher import AuditUserEnricher
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class ListAuditEntriesHandler:
	def __init__(self, read_repository: AuditReadRepository, user_repository: UserReadRepository | None = None) -> None:
		self.read_repository = read_repository
		self.user_enricher = None if user_repository is None else AuditUserEnricher(user_repository)

	async def handle(self, query: ListAuditEntriesQuery) -> list[AuditEntryDTO]:
		result = await self.read_repository.list_entries(query)
		return result if self.user_enricher is None else await self.user_enricher.entries(result)
