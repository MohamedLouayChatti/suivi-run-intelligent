from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.domain.entities.audit_entry import AuditEntry
from app.modules.audit.domain.repositories.audit_entry_repository import AuditEntryRepository
from app.modules.audit.infrastructure.persistence import mapper


class SqlAlchemyAuditEntryRepository(AuditEntryRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, entry: AuditEntry) -> None:
		self.session.add(mapper.entry_to_model(entry))
