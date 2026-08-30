from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import TypeVar

from app.shared.security.current_user import CurrentUser

ApplicationEnum = TypeVar("ApplicationEnum", bound=Enum)

_NON_WORD = re.compile(r"[^0-9a-z]+")


def compute_application_scope(
	current_user: CurrentUser, breadth_permission: str, application_enum: type[ApplicationEnum],
) -> frozenset[ApplicationEnum] | None:
	"""The same computation `app.shared.security.application_scope.require_application_scope`
	performs for a route, as a bare function a tool can call directly (a tool has no FastAPI
	request to build a Depends dependency against). None means unrestricted -- the caller holds
	`breadth_permission` -- otherwise the caller's own assigned applications.
	"""
	if current_user.has_permission(breadth_permission):
		return None
	return frozenset(
		application_enum(assignment.application.value) for assignment in current_user.application_assignments
	)


class ApplicationOutOfScope(Exception):
	"""The caller asked about an application their assignments do not cover and they hold no
	breadth permission over. Raised rather than returned so `scoped_applications` can keep a
	single return type; every tool turns it into the one refusal message below."""


APPLICATION_OUT_OF_SCOPE_ERROR = (
	"Vous n'avez pas accès aux données de cette application. Vous pouvez interroger les "
	"applications qui vous sont affectées."
)


def scoped_applications(
	current_user: CurrentUser,
	breadth_permission: str,
	application_enum: type[ApplicationEnum],
	requested: ApplicationEnum | None,
) -> frozenset[ApplicationEnum] | None:
	"""Which applications this call may actually read: the one asked for, or -- when none is
	named -- everything the caller can reach. `None` means no restriction at all.

	The intersection every analytics and ticket tool has to perform, in one place instead of
	re-derived per tool. Note what "no application named" resolves to for a caller holding the
	breadth permission: `None`, i.e. genuinely every application at once. That is the same
	"Toutes les applications" the Analytics page offers an administrator, and it is why a
	question about the whole team needs no special tool -- only a legal time range.
	"""
	allowed = compute_application_scope(current_user, breadth_permission, application_enum)
	if requested is None:
		return allowed
	if allowed is not None and requested not in allowed:
		raise ApplicationOutOfScope()
	return frozenset({requested})


def name_tokens(value: str) -> tuple[str, ...]:
	"""A person's name reduced to comparable pieces: accents folded away, case dropped, and
	every separator (space, hyphen, apostrophe, dot) treated alike.

	Accent folding is NFKD decomposition minus the combining marks, so "Bejaoui" and "Béjaoui"
	produce the same tokens -- a name typed into a chat box carries no guarantee of the accents
	the directory happens to store.
	"""
	decomposed = unicodedata.normalize("NFKD", value)
	folded = "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()
	return tuple(token for token in _NON_WORD.split(folded) if token)


def name_matches(needle: str, candidate: str) -> bool:
	"""Whether `candidate` (a stored display name) answers to `needle` (whatever the user typed).

	Order-independent and per-token, because a person is named in both orders in practice: a
	directory holding "Kraiem Yassine" must be found by "Yassine Kraiem" just as readily. Plain
	substring containment -- which this replaced -- could only ever match the one order the
	directory happened to store, so half the ways a colleague is named returned "no such
	engineer" for someone who plainly exists.

	Each typed token must prefix-match some token of the candidate, so a partial surname
	("namou") still finds its owner while an unrelated name does not.
	"""
	needle_parts = name_tokens(needle)
	if not needle_parts:
		return False
	candidate_parts = name_tokens(candidate)
	return all(
		any(part.startswith(needle_part) for part in candidate_parts) for needle_part in needle_parts
	)


def name_match_rank(needle: str, candidate: str) -> tuple[int, int]:
	"""Sort key ordering matches best-first: a candidate whose tokens are exactly the typed ones
	(in any order) outranks one merely prefixed by them, and a shorter name outranks a longer one
	carrying the same tokens. Lower is better.
	"""
	needle_parts = set(name_tokens(needle))
	candidate_parts = set(name_tokens(candidate))
	return (0 if needle_parts == candidate_parts else 1, len(candidate_parts))
