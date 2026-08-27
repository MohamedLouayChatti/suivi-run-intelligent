from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class CheckApplicationHealthCommand:
	application: Application
