from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.exceptions import InvalidAuthProviderUserId

@dataclass(frozen=True)
class AuthProviderUserId:
	"""Immutable identifier assigned by the external authentication provider."""

	value: str

	def __post_init__(self) -> None:
		if not self.value.strip():
			raise InvalidAuthProviderUserId("Auth provider user ID cannot be empty.")
