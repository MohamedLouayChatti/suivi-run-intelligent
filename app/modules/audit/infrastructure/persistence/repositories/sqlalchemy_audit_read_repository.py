from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.application.interfaces.audit_read_repository import AuditReadRepository
from app.modules.audit.application.queries.list_audit_entries.query import ListAuditEntriesQuery
from app.modules.audit.infrastructure.persistence import mapper
from app.modules.audit.infrastructure.persistence.models.audit_entry_model import AuditEntryModel


class SqlAlchemyAuditReadRepository(AuditReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_entry(self, entry_id: UUID) -> AuditEntryDTO | None:
		model = await self.session.scalar(select(AuditEntryModel).where(AuditEntryModel.id == entry_id))
		if model is None:
			return None
		return mapper.model_to_dto(model)

	async def list_entries(self, query: ListAuditEntriesQuery) -> list[AuditEntryDTO]:
		stmt = self._build_list_query(query)
		result = await self.session.scalars(stmt)
		return [mapper.model_to_dto(model) for model in result.all()]

	def _build_list_query(self, query: ListAuditEntriesQuery) -> Select[tuple[AuditEntryModel]]:
		stmt = select(AuditEntryModel)
		conditions = []
		if query.module is not None:
			conditions.append(AuditEntryModel.module == query.module)
		if query.event_type is not None:
			conditions.append(AuditEntryModel.event_type == query.event_type)
		if query.resource_type is not None:
			conditions.append(AuditEntryModel.resource_type == query.resource_type)
		if query.actor_id is not None:
			conditions.append(AuditEntryModel.actor_id == query.actor_id)
		if query.date_from is not None:
			conditions.append(AuditEntryModel.occurred_at >= query.date_from)
		if query.date_to is not None:
			conditions.append(AuditEntryModel.occurred_at <= query.date_to)
		if conditions:
			stmt = stmt.where(and_(*conditions))
		return stmt.order_by(AuditEntryModel.occurred_at.desc()).limit(query.limit).offset(query.offset)
