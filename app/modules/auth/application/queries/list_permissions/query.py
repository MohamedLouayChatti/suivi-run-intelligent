from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListPermissionsQuery:
	limit: int = 100
	offset: int = 0
