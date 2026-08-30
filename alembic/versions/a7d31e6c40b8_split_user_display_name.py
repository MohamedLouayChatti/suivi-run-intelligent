"""Split users.display_name into first_name and last_name

Revision ID: a7d31e6c40b8
Revises: ee12415165af
Create Date: 2026-08-30

One column held a whole name and every layer had to guess where the boundary fell: the Clerk
webhook joined the provider's two fields with a space, the settings form split the result on
the first one, and those two are not inverses for anyone whose given name or surname runs to
more than one word. The full name is derived from these two columns now, so nothing guesses.

Backfilling has to undo a join that was never reversible, over rows written under two
different conventions -- so the split rule is chosen per row from evidence the row carries:

* Rows whose `auth_provider_user_id` starts with `user_` came from Clerk, where the stored
  string is exactly `first_name + " " + last_name`. The first token is therefore the given
  name and the remainder the surname, which reproduces what Clerk itself holds.

* Every other row was written by the historical-user seeder, whose names follow the ticket
  exports' convention of capitalising the surname and writing it first. The leading run of
  ALL-CAPS tokens is the surname -- which is what gets `BEN JEDDI`, `BEN MBAREK`, `BEN TAHER`
  and `PIERROT CALLIZO` right where "first token" would not, and equally what keeps
  `BAFFOUN Mohamed Ali` from losing half a given name.

Three rows carry no usable evidence and are named outright below.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7d31e6c40b8"
down_revision = "ee12415165af"
branch_labels = None
depends_on = None


_CLERK_PROVIDER_PREFIX = "user_"

# Rows the two rules above cannot settle, decided by hand.
#
# The first two are the only seeded engineers recorded given-name-first, so the capitalisation
# rule has nothing to read. The third is a real Clerk account whose owner had typed their
# surname into the provider's "first name" field; that has since been corrected at Clerk and
# the correction has already arrived here, so this entry now only covers a database where it
# has not -- mirroring the uncorrected form would spell them "Ala NAMOUCHI" and stop the
# historical import files naming them.
_BY_HAND: dict[str, tuple[str, str]] = {
	"Akram Sahli": ("Akram", "Sahli"),
	"Mariem Hammami": ("Mariem", "Hammami"),
	"NAMOUCHI Ala": ("Ala", "NAMOUCHI"),
}


def _split(display_name: str, auth_provider_user_id: str) -> tuple[str, str]:
	name = " ".join(display_name.split())
	if name in _BY_HAND:
		return _BY_HAND[name]

	tokens = name.split(" ")
	if not tokens or tokens == [""]:
		return "", ""
	if len(tokens) == 1:
		# A lone token is a surname under this ordering, and it is all we are told either way.
		return "", tokens[0]

	if not auth_provider_user_id.startswith(_CLERK_PROVIDER_PREFIX):
		surname_length = 0
		for token in tokens:
			if token.isupper() and any(character.isalpha() for character in token):
				surname_length += 1
			else:
				break
		if 0 < surname_length < len(tokens):
			return " ".join(tokens[surname_length:]), " ".join(tokens[:surname_length])

	return tokens[0], " ".join(tokens[1:])


def upgrade() -> None:
	op.add_column("users", sa.Column("first_name", sa.String(length=255), nullable=True))
	op.add_column("users", sa.Column("last_name", sa.String(length=255), nullable=True))

	connection = op.get_bind()
	rows = connection.execute(
		sa.text("SELECT id, display_name, auth_provider_user_id FROM users")
	).all()
	for row in rows:
		first_name, last_name = _split(row.display_name or "", row.auth_provider_user_id or "")
		connection.execute(
			sa.text("UPDATE users SET first_name = :first, last_name = :last WHERE id = :id"),
			{"first": first_name, "last": last_name, "id": row.id},
		)

	op.alter_column("users", "first_name", nullable=False)
	op.alter_column("users", "last_name", nullable=False)
	op.drop_column("users", "display_name")


def downgrade() -> None:
	op.add_column("users", sa.Column("display_name", sa.String(length=255), nullable=True))
	# The same composition the domain applies, so a downgraded row reads as it did before.
	op.execute(
		"UPDATE users SET display_name = btrim(concat_ws(' ', last_name, first_name))"
	)
	op.alter_column("users", "display_name", nullable=False)
	op.drop_column("users", "first_name")
	op.drop_column("users", "last_name")
