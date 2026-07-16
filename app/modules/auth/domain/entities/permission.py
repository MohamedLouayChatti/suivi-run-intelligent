from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Permission:
	"""Reference-data entity representing an authorization capability."""

	id: UUID
	name: str
	description: str
