from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class PermissionRevokedFromUser(DomainEvent):
	user_id: UUID
	permission_id: UUID
