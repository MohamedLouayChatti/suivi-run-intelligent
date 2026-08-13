from __future__ import annotations

from enum import StrEnum


class IdentifierType(StrEnum):
	"""Kinds of organization-specific identifier found inside ticket descriptions.

	Every member is stripped from the text that gets embedded (its digits carry no meaning a
	multilingual model can use, and near-identical digit runs pull unrelated tickets together)
	and kept as structured data for exact retrieval instead.

	The members differ in what an *exact match* on them is worth, which `is_reference` captures:
	a reference identifier names another business object the ticket is explicitly about, so two
	tickets citing the same one are related by construction. The rest merely co-occur -- the same
	user filing two unrelated tickets, or two unrelated incidents on one site.
	"""

	# Reference families -- a shared value means the two tickets are about the same thing.
	INCIDENT_REF = "INCIDENT_REF"
	ORDER_REF = "ORDER_REF"
	PRESTATION_REF = "PRESTATION_REF"

	# Instance families -- unique per occurrence, useful for lookup, meaningless for similarity.
	TRANSFER_ID = "TRANSFER_ID"
	JOB_RUN_ID = "JOB_RUN_ID"

	# Context families -- shared values are common but say nothing about the incident itself.
	USER_CUID = "USER_CUID"
	SITE_CODE = "SITE_CODE"
	BUILDING_CODE = "BUILDING_CODE"
	LINK_CODE = "LINK_CODE"

	@property
	def is_reference(self) -> bool:
		"""Whether an exact match on this type is strong enough to guarantee a result slot.

		Measured on the 799-ticket historical corpus: restricting the guarantee to these three
		recovers the follow-up tickets vector search cannot reach ("Au sujet du ticket
		INC001010976766" has no problem text at all, so its target ranks 114th-222nd by cosine)
		while admitting none of the eight same-user/different-problem pairs that USER_CUID alone
		would have forced into results.
		"""
		return self in _REFERENCE_TYPES


_REFERENCE_TYPES = frozenset(
	{IdentifierType.INCIDENT_REF, IdentifierType.ORDER_REF, IdentifierType.PRESTATION_REF}
)
