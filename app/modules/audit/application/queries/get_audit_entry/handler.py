from __future__ import annotations

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.application.exceptions import AuditEntryNotFound
from app.modules.audit.application.interfaces.audit_read_repository import AuditReadRepository
from app.modules.audit.application.queries.get_audit_entry.query import GetAuditEntryQuery
from app.modules.audit.application.queries.user_enricher import AuditUserEnricher
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class GetAuditEntryHandler:
	def __init__(self, read_repository: AuditReadRepository, user_repository: UserReadRepository | None = None) -> None:
		self.read_repository = read_repository
		self.user_enricher = None if user_repository is None else AuditUserEnricher(user_repository)

	async def handle(self, query: GetAuditEntryQuery) -> AuditEntryDTO:
		entry = await self.read_repository.get_entry(query.entry_id)
		if entry is None:
			raise AuditEntryNotFound()
		return entry if self.user_enricher is None else await self.user_enricher.entry(entry)
