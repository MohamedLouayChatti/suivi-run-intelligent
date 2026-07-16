from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId


class UserRepository(ABC):
	@abstractmethod
	async def add(self, user: User) -> None: ...

	@abstractmethod
	async def get_by_id(self, user_id: UUID) -> User | None: ...

	@abstractmethod
	async def get_by_auth_provider_user_id(self, auth_provider_user_id: AuthProviderUserId) -> User | None: ...

	@abstractmethod
	async def get_by_email(self, email: str) -> User | None: ...

	@abstractmethod
	async def update(self, user: User) -> None: ...

	@abstractmethod
	async def exists(self, user_id: UUID) -> bool: ...
