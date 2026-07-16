from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class UserCreated(DomainEvent):
	user_id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	display_name: str
