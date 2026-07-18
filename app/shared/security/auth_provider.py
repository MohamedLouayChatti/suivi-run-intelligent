from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AuthenticatedClaims:
	"""Provider-independent claims produced by a successful authentication."""

	subject: str
	issuer: str
	audience: str | tuple[str, ...] | None
	claims: Mapping[str, Any]

	def __post_init__(self) -> None:
		object.__setattr__(self, "claims", MappingProxyType(dict(self.claims)))


class AuthProvider(ABC):
	"""Port for authenticating bearer tokens without exposing provider details.

	It owns the authentication contract only; it does not load users, authorize
	requests, or persist authentication state.
	"""

	@abstractmethod
	def authenticate(self, token: str) -> AuthenticatedClaims:
		"""Validate a token and return its provider-independent claims."""
		raise NotImplementedError
