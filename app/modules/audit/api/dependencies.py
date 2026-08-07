from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.modules.audit.application.queries.export_audit_entries.handler import ExportAuditEntriesHandler
from app.modules.audit.application.queries.get_audit_entry.handler import GetAuditEntryHandler
from app.modules.audit.application.queries.list_audit_entries.handler import ListAuditEntriesHandler
from app.modules.audit.infrastructure.persistence.repositories.sqlalchemy_audit_read_repository import SqlAlchemyAuditReadRepository
from app.modules.auth.api.dependencies import get_user_read_repository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import SqlAlchemyUserReadRepository
from app.shared.database.session import create_session


async def get_read_repository() -> AsyncIterator[SqlAlchemyAuditReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyAuditReadRepository(session)
	finally:
		await session.close()


def get_list_audit_entries_handler(
	repository: Annotated[SqlAlchemyAuditReadRepository, Depends(get_read_repository)],
	users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)],
) -> ListAuditEntriesHandler:
	return ListAuditEntriesHandler(repository, users)


def get_get_audit_entry_handler(
	repository: Annotated[SqlAlchemyAuditReadRepository, Depends(get_read_repository)],
	users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)],
) -> GetAuditEntryHandler:
	return GetAuditEntryHandler(repository, users)


def get_export_audit_entries_handler(
	repository: Annotated[SqlAlchemyAuditReadRepository, Depends(get_read_repository)],
	users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)],
) -> ExportAuditEntriesHandler:
	return ExportAuditEntriesHandler(repository, users)
