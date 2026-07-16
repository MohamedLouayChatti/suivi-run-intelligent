from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RevokeRoleCommand:
	user_id: UUID
	role_id: UUID
