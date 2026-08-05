from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.audit.api import dependencies as dep
from app.modules.audit.api.schemas import AuditEntryResponse
from app.modules.audit.application.queries.get_audit_entry.query import GetAuditEntryQuery
from app.modules.audit.application.queries.list_audit_entries.query import ListAuditEntriesQuery
from app.shared.security.permissions import require_admin, require_permissions

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditEntryResponse], dependencies=[Depends(require_permissions("audit.read")), Depends(require_admin())])
async def list_audit_entries(
	handler=Depends(dep.get_list_audit_entries_handler),
	module: str | None = None,
	event_type: str | None = None,
	resource_type: str | None = None,
	actor_id: UUID | None = None,
	date_from: datetime | None = None,
	date_to: datetime | None = None,
	page: Annotated[int, Query(ge=1)] = 1,
	page_size: Annotated[int, Query(ge=1, le=100)] = 100,
):
	query = ListAuditEntriesQuery(
		module=module, event_type=event_type, resource_type=resource_type, actor_id=actor_id,
		date_from=date_from, date_to=date_to, limit=page_size, offset=(page - 1) * page_size,
	)
	return [AuditEntryResponse.from_dto(entry) for entry in await handler.handle(query)]


@router.get("/{entry_id}", response_model=AuditEntryResponse, dependencies=[Depends(require_permissions("audit.read")), Depends(require_admin())])
async def get_audit_entry(entry_id: UUID, handler=Depends(dep.get_get_audit_entry_handler)):
	return AuditEntryResponse.from_dto(await handler.handle(GetAuditEntryQuery(entry_id)))
