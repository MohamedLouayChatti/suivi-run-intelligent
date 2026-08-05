from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RevokePermissionFromRoleCommand:
	role_id: UUID
	permission_id: UUID
	actor_id: UUID
