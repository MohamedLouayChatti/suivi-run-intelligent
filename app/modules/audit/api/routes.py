from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.modules.audit.api import dependencies as dep
from app.modules.audit.api.schemas import AuditEntryResponse
from app.modules.audit.application.queries.export_audit_entries.query import ExportAuditEntriesQuery
from app.modules.audit.application.queries.get_audit_entry.query import GetAuditEntryQuery
from app.modules.audit.application.queries.list_audit_entries.query import ListAuditEntriesQuery
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditEntryResponse], dependencies=[Depends(require_permissions("audit.read"))])
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


@router.get("/export", dependencies=[Depends(require_permissions("audit.read"))])
async def export_audit_entries(handler=Depends(dep.get_export_audit_entries_handler), module: str | None = None):
	query = ExportAuditEntriesQuery(module=module)
	entries = await handler.handle(query)

	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(["ID", "Horodatage", "Module", "Type d'événement", "Action", "Type de ressource", "Acteur", "Détails"])
	for entry in entries:
		writer.writerow([
			str(entry.id), entry.occurred_at.isoformat(), entry.module, entry.event_type, entry.action,
			entry.resource_type or "", entry.actor.display_name if entry.actor else (entry.actor_label or ""),
			json.dumps(entry.payload, ensure_ascii=False),
		])
	content = buffer.getvalue().encode("utf-8-sig")
	return Response(
		content=content,
		media_type="text/csv",
		headers={"Content-Disposition": 'attachment; filename="journal_audit.csv"'},
	)


@router.get("/{entry_id}", response_model=AuditEntryResponse, dependencies=[Depends(require_permissions("audit.read"))])
async def get_audit_entry(entry_id: UUID, handler=Depends(dep.get_get_audit_entry_handler)):
	return AuditEntryResponse.from_dto(await handler.handle(GetAuditEntryQuery(entry_id)))
