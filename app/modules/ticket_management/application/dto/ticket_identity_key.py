from __future__ import annotations

from dataclasses import dataclass


def normalize_identity_text(value: str | None) -> str:
	"""Collapse a value to the form the duplicate check compares.

	Trimmed, internally whitespace-collapsed and lower-cased, with absent treated as empty. Two
	exports of the same incident routinely differ by a trailing space or a line Excel reflowed,
	and those are not two incidents. `lower()` rather than `casefold()` deliberately: the
	comparison also has to be expressible in SQL against tickets already stored, and Postgres'
	`lower()` is the counterpart that exists there.
	"""
	if value is None:
		return ""
	return " ".join(value.split()).lower()


@dataclass(frozen=True)
class TicketIdentityKey:
	"""What makes two tickets the same incident for the purposes of an import.

	All three parts together, never one of them alone: `genergy_id` and `oceane_id` carry no unique
	constraint in this module and are legitimately absent on plenty of tickets, so either on its
	own would reject rows that are genuinely distinct. Absent identifiers compare as empty rather
	than being excluded from the check -- an export with no identifiers at all is exactly the file
	most likely to be uploaded twice.
	"""

	genergy_id: str
	oceane_id: str
	description: str

	@classmethod
	def of(cls, *, genergy_id: str | None, oceane_id: str | None, description: str) -> TicketIdentityKey:
		return cls(
			genergy_id=normalize_identity_text(genergy_id),
			oceane_id=normalize_identity_text(oceane_id),
			description=normalize_identity_text(description),
		)
