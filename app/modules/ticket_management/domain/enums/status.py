from __future__ import annotations

from enum import StrEnum


class Status(StrEnum):
	OPEN = "OPEN"
	IN_PROGRESS = "IN_PROGRESS"
	PENDING = "PENDING"
	RESOLVED = "RESOLVED"
	CLOSED = "CLOSED"
