from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AssignRoleCommand:
	user_id: UUID
	role_id: UUID
	actor_id: UUID
