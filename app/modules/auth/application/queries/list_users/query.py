from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListUsersQuery:
	limit: int = 100
	offset: int = 0
