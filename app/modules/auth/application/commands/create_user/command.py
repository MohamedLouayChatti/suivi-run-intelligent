from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId


@dataclass(frozen=True)
class CreateUserCommand:
	user_id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	first_name: str
	last_name: str
	"""The two halves of the name, as the identity provider holds them.

	Carried apart rather than pre-joined so that the rule for writing a full name lives in one
	place -- the domain -- instead of in whichever adapter happened to receive the two fields.
	"""
	avatar_url: str | None = None
	declared_application: str | None = None
	"""The application the applicant chose for themselves on the signup form, unparsed.

	Raw text rather than an `Application`, and self-declared rather than assigned: a person
	signing up types this about themselves before anyone has approved them, so it may name
	an application that does not exist or none at all.  Turning it into an assignment, and
	deciding what a missing or unusable answer means, is the handler's job -- the same
	division `ImportTicketsCommand` makes by carrying a file's records as raw text.
	"""
	declared_functional_team: str | None = None
	"""The functional team the applicant chose for themselves, unparsed. See above."""
	actor_id: UUID | None = None
