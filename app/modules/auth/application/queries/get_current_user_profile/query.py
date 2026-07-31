from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetCurrentUserProfileQuery:
	user_id: UUID
