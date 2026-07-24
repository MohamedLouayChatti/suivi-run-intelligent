from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.assignment_type import AssignmentType


@dataclass(frozen=True, slots=True)
class ApplicationAssignment:
	application: Application
	assignment_type: AssignmentType
