from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListRolesQuery:
	limit: int = 100
	offset: int = 0
