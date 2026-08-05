from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.audit.domain.entities.audit_entry import AuditEntry


class AuditEntryRepository(ABC):
	@abstractmethod
	async def add(self, entry: AuditEntry) -> None:
		raise NotImplementedError
