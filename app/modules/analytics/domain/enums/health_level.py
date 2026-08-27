from __future__ import annotations

from enum import StrEnum


class HealthLevel(StrEnum):
	GOOD = "good"
	WARNING = "warning"
	CRITICAL = "critical"
