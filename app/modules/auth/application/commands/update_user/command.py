from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UpdateUserCommand:
	user_id: UUID
	email: str | None = None
	display_name: str | None = None
