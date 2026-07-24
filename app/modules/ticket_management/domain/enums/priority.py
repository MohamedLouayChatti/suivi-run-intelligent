from __future__ import annotations

from enum import StrEnum


class Priority(StrEnum):
	LOW = "P4"
	MEDIUM = "P3"
	HIGH = "P2"
	CRITICAL = "P1"
