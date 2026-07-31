from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId


@dataclass(frozen=True)
class CurrentUserProfileDTO:
	id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	display_name: str
	functional_team: FunctionalTeam
	application_assignments: frozenset[ApplicationAssignment] = field(default_factory=frozenset)
	roles: list[RoleDTO] = field(default_factory=list)
	effective_permissions: list[PermissionDTO] = field(default_factory=list)
