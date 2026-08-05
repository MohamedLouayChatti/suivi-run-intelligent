from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserSummaryDTO:
	"""The small user projection needed by Audit read models."""

	id: UUID
	display_name: str
	avatar_url: str | None = None
