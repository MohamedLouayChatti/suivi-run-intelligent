from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from app.shared.security.authorization_result import AuthorizationResult
if TYPE_CHECKING:
	from app.shared.security.current_user import CurrentUser


class InstanceAuthorizationPolicy(ABC):
	@abstractmethod
	async def authorize(
		self,
		*,
		current_user: CurrentUser,
		resource_id: Any,
		operation: str,
	) -> AuthorizationResult:
		raise NotImplementedError
