from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern

from app.modules.knowledge_base.domain.enums.identifier_type import IdentifierType


@dataclass(frozen=True)
class ExtractedIdentifier:
	"""One organization-specific identifier lifted out of a description. `value` is normalized to
	upper case so a lower-cased citation still matches the canonical form during exact retrieval.
	"""

	type: IdentifierType
	value: str


@dataclass(frozen=True)
class PreprocessedDescription:
	"""The three views of one description the pipeline needs.

	`original` is returned untouched and is what the user always sees -- preprocessing never
	rewrites a ticket's description, it only decides what text gets embedded.
	"""

	original: str
	embedding_text: str
	identifiers: tuple[ExtractedIdentifier, ...]


@dataclass(frozen=True)
class _Rule:
	"""A single deterministic substitution. The regex must expose the identifier as group `id`;
	an optional group `keep` holds surrounding text that stays in the embedded output (used by
	JOB_RUN_ID, whose digits are only recognizable by their `RUNID :` prefix).
	"""

	type: IdentifierType
	pattern: Pattern[str]
	placeholder: str


# Order matters: longer, more specific families must run first so a broader rule cannot consume
# part of them (BUILDING_CODE before SITE_CODE, PRESTATION_REF before TRANSFER_ID).
#
# The reference families are matched case-insensitively -- an 11-digit run behind an `F` is
# unambiguous whatever its case, and descriptions are inconsistently upper-cased. The short
# context families stay case-sensitive: `[A-Z]{4}\d{4}` matched loosely would swallow ordinary
# words followed by a number.
_RULES: tuple[_Rule, ...] = (
	_Rule(
		IdentifierType.BUILDING_CODE,
		re.compile(r"(?P<id>\bIMB/\d{5}/[A-Z]/[A-Z0-9]{4}\b)"),
		"<code_immeuble>",
	),
	_Rule(
		IdentifierType.PRESTATION_REF,
		re.compile(r"(?P<id>\bCOL\d{17}\b)", re.IGNORECASE),
		"<ref_prestation>",
	),
	_Rule(
		IdentifierType.INCIDENT_REF,
		re.compile(r"(?P<id>\bINC\d{12}\b)", re.IGNORECASE),
		"<ref_incident>",
	),
	_Rule(
		IdentifierType.ORDER_REF,
		re.compile(r"(?P<id>\bF\d{11}\b)", re.IGNORECASE),
		"<ref_commande>",
	),
	_Rule(
		IdentifierType.JOB_RUN_ID,
		re.compile(r"(?P<keep>\bRUNID\s*:\s*)(?P<id>\d{6,12}\b)", re.IGNORECASE),
		"<ref_execution>",
	),
	_Rule(
		IdentifierType.TRANSFER_ID,
		re.compile(r"(?P<id>\b[A-Z]\d{7}\b)"),
		"<ref_transfert>",
	),
	_Rule(
		IdentifierType.USER_CUID,
		re.compile(r"(?P<id>\b[A-Z]{4}\d{4}\b)"),
		"<code_utilisateur>",
	),
	_Rule(
		IdentifierType.SITE_CODE,
		re.compile(r"(?P<id>\b\d{5}[A-Z]{3}\b)"),
		"<code_site>",
	),
	_Rule(
		IdentifierType.LINK_CODE,
		re.compile(r"(?P<id>\b\d{4}[A-Z]{3}\d\b)"),
		"<code_lien>",
	),
)

# Dates and times are instance noise for the same reason identifiers are, but nothing ever needs
# to retrieve by them, so they are normalized without being recorded as identifiers.
_NOISE_SUBSTITUTIONS: tuple[tuple[Pattern[str], str], ...] = (
	(re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "<date>"),
	(re.compile(r"\b\d{1,2}h\d{2}\b"), "<heure>"),
)

_HORIZONTAL_WHITESPACE = re.compile(r"[^\S\n]+")


def preprocess_description(description: str) -> PreprocessedDescription:
	"""Split a raw description into the text to embed and the identifiers to index.

	Pure and deterministic: the same input always yields the same output, with no I/O, no clock
	and no model involved. That is what lets ingestion and query-time preprocessing be identical
	by construction -- they are literally this one call -- and it is why identifier policy lives
	here rather than inside the embedding provider, which only ever turns text into a vector.

	Identifiers are replaced by a French type placeholder rather than deleted. Deleting them
	collapsed 34 of the 799 historical descriptions to three words or fewer and four to almost
	nothing ("cde", "suite ticket"); the placeholder keeps the sentence intact and keeps the
	signal that *a* commande was referenced, while discarding the digits that were creating
	spurious similarity between unrelated orders.
	"""
	if not description:
		return PreprocessedDescription(original=description, embedding_text=description, identifiers=())

	identifiers: list[ExtractedIdentifier] = []
	seen: set[tuple[IdentifierType, str]] = set()
	text = description

	for rule in _RULES:

		def replace(match: re.Match[str], rule: _Rule = rule) -> str:
			key = (rule.type, match.group("id").upper())
			if key not in seen:
				seen.add(key)
				identifiers.append(ExtractedIdentifier(type=key[0], value=key[1]))
			kept = match.groupdict().get("keep") or ""
			return f"{kept}{rule.placeholder}"

		text = rule.pattern.sub(replace, text)

	for pattern, placeholder in _NOISE_SUBSTITUTIONS:
		text = pattern.sub(placeholder, text)

	# Substitutions leave doubled spaces behind; newlines are preserved because the supervision
	# alarm descriptions are line-structured and that structure is real content.
	embedding_text = _HORIZONTAL_WHITESPACE.sub(" ", text).strip()

	return PreprocessedDescription(
		original=description,
		embedding_text=embedding_text,
		identifiers=tuple(identifiers),
	)
