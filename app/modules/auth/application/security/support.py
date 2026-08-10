from __future__ import annotations

from uuid import UUID

USER_READ_ALL_PERMISSION = "user.read_all"
"""Breadth permission: read any user's full record, not just one's own."""

ROLE_READ_ALL_PERMISSION = "role.read_all"
"""Breadth permission: read any role and its permissions, not just the ones one holds."""


def parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None
