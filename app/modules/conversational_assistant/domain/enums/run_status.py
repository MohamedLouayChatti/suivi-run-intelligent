from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
	PENDING = "PENDING"
	RUNNING = "RUNNING"
	COMPLETED = "COMPLETED"
	FAILED = "FAILED"
