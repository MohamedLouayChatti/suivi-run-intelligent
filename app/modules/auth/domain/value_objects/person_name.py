from __future__ import annotations


def normalize_name_part(value: str) -> str:
	"""One half of a name, with its whitespace collapsed to single spaces.

	Applied to what an identity provider hands us rather than trusted as given: a surname
	arrives as `" BEN  JEDDI "` often enough, and two spellings of one name differing only in
	whitespace would otherwise be two different people to every comparison below. Bare
	`split()` is what does it -- it breaks on runs of any whitespace and drops the empty parts,
	which is exactly the normalization a name wants: a sequence of tokens, and how many spaces
	someone typed between them is not part of it.
	"""
	return " ".join(value.split())


def compose_display_name(first_name: str, last_name: str) -> str:
	"""The one spelling of a person's full name, in the order this organization writes it.

	Surname first -- `"BEN JEDDI Cyrine"`, not `"Cyrine BEN JEDDI"`. That is the convention of
	the historical ticket exports the batch import reads and of every seeded engineer, so it
	is the order a name has to be written in for those files to still name the people they
	name.

	Written here, once, rather than wherever a full name is needed: this used to be spelled by
	the webhook adapter joining the provider's two fields and un-spelled by the settings form
	splitting on the first space, and those two are not inverses -- a first name of two words
	round-tripped into a different person's name on a save that changed nothing.

	Either half may be empty (an identity provider does not require both), in which case this
	is the other half alone rather than a string with a stray space in it.
	"""
	return " ".join(part for part in (normalize_name_part(last_name), normalize_name_part(first_name)) if part)


def name_orderings(first_name: str, last_name: str) -> tuple[str, ...]:
	"""Both orders a person's full name is written in, lowercased for comparison.

	A person is named in both orders in practice -- the same fact `name_matches` in the
	conversational assistant's tool support was written for -- and a spreadsheet filled in by
	hand is exactly where the other order turns up. Two orderings rather than a set of tokens
	compared in any arrangement: a full name here is composed of exactly two halves, so the
	only rearrangement that occurs is swapping them. Nobody writes a surname's second word
	before the given name.

	Deduplicated, because a person with only one half recorded has one spelling, not two.
	"""
	forward = compose_display_name(first_name, last_name).lower()
	reversed_ = " ".join(
		part for part in (normalize_name_part(first_name), normalize_name_part(last_name)) if part
	).lower()
	return (forward,) if forward == reversed_ else (forward, reversed_)


def normalize_full_name(value: str) -> str:
	"""A full name as written by someone else, in the form `name_orderings` produces."""
	return normalize_name_part(value).lower()
