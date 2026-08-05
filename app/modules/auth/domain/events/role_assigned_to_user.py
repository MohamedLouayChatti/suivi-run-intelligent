from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class RoleAssignedToUser(DomainEvent):
	user_id: UUID
	role_id: UUID
	actor_id: UUID
