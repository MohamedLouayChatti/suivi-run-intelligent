from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GrantPermissionToRoleCommand:
	role_id: UUID
	permission_id: UUID
