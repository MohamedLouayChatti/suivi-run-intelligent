from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

# The column contract of an imported file, named once here because three things depend on it
# agreeing exactly: the header check, the per-cell parsing, and the message an operator reads when a
# column is wrong.
#
# The headers are French because the people filling these sheets work in French and the exports they
# start from already are -- `Acteur`, `Statut`, `Date d'ouverture` and `Actions réalisées` are
# borrowed from those exports verbatim rather than invented. The constants keep their English names,
# because they are code and the rest of the module is written in English; only their *values*, the
# text an operator types into a header cell, are French. Nothing downstream reads a header: records
# are re-keyed onto these canonical names before parsing, so the parser, the aggregate and the error
# messages all speak one vocabulary.
#
# The rejection messages built from these names are French too, for the same reason the names are:
# they are read by the person editing the spreadsheet, not by a developer. The dividing line across
# both this module and the knowledge base's import is who reads the string -- a message that reaches
# the import report is French, and everything only a developer sees (log lines, docstrings, the
# CLI's own output, exception type names) stays English like the rest of the code.
TITLE = "titre"
DESCRIPTION = "description"
PRIORITY = "priorité"
CATEGORY = "catégorie"
FUNCTIONAL_TEAM = "équipe fonctionnelle"
ASSIGNEE = "acteur"
CREATED_AT = "date d'ouverture"

STATUS = "statut"
GENERGY_ID = "id genergy"
OCEANE_ID = "id oceane"
REQUIRES_JIRA = "jira requis"
JIRA_ID = "id jira"
JIRA_DELIVERY_DATE = "date de livraison jira"
OPERATIONAL_HIGHLIGHT = "point d'attention"
OFFER = "offre"
VERSION = "version"
ELEMENT = "élément"
VIO_APP = "application vio"
RESOLVED_AT = "date de résolution"
CLOSED_AT = "date de clôture"
RESOLUTION_NOTES = "actions réalisées"
TRANSFERRED_TO = "transféré à"

# `acteur` is the one column that does not correspond to a Ticket field one-for-one: the aggregate
# stores an assignee_id, and nobody filling a spreadsheet has user UUIDs. It carries the display
# name, resolved against the users already in the database -- and rejected when it matches nobody,
# or more than one person, since display names carry no unique constraint.
REQUIRED_COLUMNS: tuple[str, ...] = (
	TITLE, DESCRIPTION, PRIORITY, CATEGORY, FUNCTIONAL_TEAM, ASSIGNEE, CREATED_AT,
)

OPTIONAL_COLUMNS: tuple[str, ...] = (
	STATUS, GENERGY_ID, OCEANE_ID, REQUIRES_JIRA, JIRA_ID, JIRA_DELIVERY_DATE,
	OPERATIONAL_HIGHLIGHT, OFFER, VERSION, ELEMENT, VIO_APP,
	RESOLVED_AT, CLOSED_AT, RESOLUTION_NOTES, TRANSFERRED_TO,
)

KNOWN_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

# Alternative spellings that resolve to the same column. Only the ones normalization cannot reach on
# its own are listed: `equipe_fonctionnelle` and `priorite` already normalize onto their accented
# forms, while `date_ouverture` does not, because the elided article in `date d'ouverture` is a real
# difference between the two rather than a matter of punctuation. Also here: the headers the team's
# own exports actually carry, typo included -- `Actions réalisés` is how that column is spelled in
# every file they have, and rejecting it would mean asking them to fix a header they did not write.
_ALIASES: dict[str, tuple[str, ...]] = {
	CREATED_AT: ("date ouverture", "date de creation", "date creation"),
	RESOLVED_AT: ("date resolution",),
	CLOSED_AT: ("date cloture", "date de fermeture", "date fermeture"),
	JIRA_DELIVERY_DATE: ("date livraison jira", "date de livraison"),
	OPERATIONAL_HIGHLIGHT: ("point attention",),
	RESOLUTION_NOTES: ("actions réalisés", "actions"),
	GENERGY_ID: ("id ticket genergy", "genergy"),
	OCEANE_ID: ("id ticket oceane", "oceane"),
	OFFER: ("offre composée",),
	CATEGORY: ("catégorie d'incident", "categorie incident"),
	ASSIGNEE: ("assigné à", "assignee"),
	FUNCTIONAL_TEAM: ("équipe",),
	VIO_APP: ("app vio",),
	TRANSFERRED_TO: ("transféré vers", "transfert"),
}

# Refused rather than ignored, and for two different reasons. `application` is answered by the
# uploader for the whole file, so a column could only ever contradict them and there is no useful
# behaviour for the case where the two disagree. The others are the aggregate's own bookkeeping,
# which a file may not assert.
_REJECTED_COLUMNS: dict[str, str] = {
	"application": "l'application est choisie au moment du dépôt du fichier, pas ligne par ligne",
	"id": "les identifiants de ticket sont générés par l'import",
	"identifiant": "les identifiants de ticket sont générés par l'import",
	"date de mise à jour": "cette date est tenue à jour par le ticket lui-même",
	"date d'archivage": "l'archivage ne fait pas partie d'un import",
}


def _quoted(name: str) -> str:
	"""A column name as it appears inside a message -- French quotation marks rather than `repr`,
	so the report reads the way the rest of the interface does."""
	return f"« {name} »"


def normalize_header(text: str) -> str:
	"""Reduce a header cell to the form column matching compares.

	Accents stripped, case folded, and everything that is not a letter or a digit removed -- so
	`Date d'ouverture`, `DATE D OUVERTURE` and `date douverture` are one column, and a header
	retyped without its accent or its apostrophe still lands. This can only ever forgive
	punctuation, never map a column to the wrong field: no two names in the contract differ solely
	by the characters it discards, which `_build_lookup` refuses to let anyone introduce.
	"""
	decomposed = unicodedata.normalize("NFKD", text)
	without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
	return "".join(char for char in without_accents.casefold() if char.isalnum())


def _build_lookup() -> dict[str, str]:
	"""Every accepted spelling, normalized, pointing at the column it names.

	Raises rather than silently overwriting when two *different* columns would share a key. That is
	the one failure the forgiving match could introduce -- two columns quietly becoming one -- and
	catching it at import time means a bad alias cannot ship, where discovering it later means a
	file whose `élément` landed somewhere else. Repeats within a single column are simply
	deduplicated: an alias that normalization already covers is redundant, not dangerous.
	"""
	lookup: dict[str, str] = {}
	for column in KNOWN_COLUMNS:
		for spelling in (column, *_ALIASES.get(column, ())):
			key = normalize_header(spelling)
			existing = lookup.get(key)
			if existing is not None and existing != column:
				raise AssertionError(
					f"Column spellings {existing!r} and {column!r} both normalize to {key!r}."
				)
			lookup[key] = column
	return lookup


_COLUMN_BY_NORMALIZED_HEADER = _build_lookup()
_REJECTED_BY_NORMALIZED_HEADER = {
	normalize_header(header): reason for header, reason in _REJECTED_COLUMNS.items()
}


@dataclass(frozen=True)
class ResolvedColumns:
	"""What the header row turned out to be: each header cell mapped to the column it names, plus
	every problem with the row as a whole.

	Both halves come back together because they are one pass over one row, and because a caller with
	problems to report has no use for a partial mapping -- a file whose header cannot be resolved is
	rejected before any of its rows are read.
	"""

	by_header: dict[str, str] = field(default_factory=dict)
	problems: list[str] = field(default_factory=list)


def resolve_columns(headers: tuple[str, ...]) -> ResolvedColumns:
	"""Map each header cell onto the column it names, reporting everything wrong with the row.

	Reported all at once, and separately from the records below: a header this file cannot be read
	against makes every row's errors noise, so the caller stops here rather than reporting a
	thousand rows' worth of consequences of one misspelled column.
	"""
	resolved = ResolvedColumns()
	claimed: dict[str, str] = {}

	for header in headers:
		if not header.strip():
			continue
		normalized = normalize_header(header)
		column = _COLUMN_BY_NORMALIZED_HEADER.get(normalized)
		if column is None:
			reason = _REJECTED_BY_NORMALIZED_HEADER.get(normalized)
			if reason is not None:
				resolved.problems.append(
					f"La colonne {_quoted(header)} n'est pas acceptée : {reason}."
				)
			else:
				resolved.problems.append(
					f"Colonne inconnue : {_quoted(header)}. Corrigez son intitulé ou supprimez-la."
				)
			continue
		if column in claimed:
			# Two spellings of one column is still one column twice, and picking either would
			# silently discard whichever the file meant to be authoritative.
			resolved.problems.append(
				f"Les colonnes {_quoted(claimed[column])} et {_quoted(header)} désignent toutes les "
				f"deux {_quoted(column)}. Conservez-en une seule."
			)
			continue
		claimed[column] = header
		resolved.by_header[header] = column

	missing = [column for column in REQUIRED_COLUMNS if column not in claimed]
	if missing:
		resolved.problems.append(
			f"Colonne(s) obligatoire(s) manquante(s) : {', '.join(_quoted(c) for c in missing)}."
		)

	return resolved
