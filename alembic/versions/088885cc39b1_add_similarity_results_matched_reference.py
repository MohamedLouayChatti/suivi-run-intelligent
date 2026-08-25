"""add similarity_results matched_reference

Revision ID: 088885cc39b1
Revises: bfaa6afb4b48
Create Date: 2026-08-25 17:49:37.619055

A row's rank alone cannot say why it outranks another: `rank_candidates`
(domain/services/similarity_ranking.py) guarantees every reference-matched candidate a slot ahead
of every semantic one, regardless of its own cosine score, because a ticket the query explicitly
cites is related whatever the cosine says. `RankedCandidate.matched_reference` already carried that
distinction but was dropped before persistence, so a citation with a low score could sit above a
higher-scoring semantic match with nothing in the stored data -- or the API response -- explaining
why. This column keeps the flag through persistence so the read side can label it instead of
presenting a bare, apparently-contradictory percentage.

Added with a server_default of false so the column can be NOT NULL on a table that already has
rows. Nothing is backfilled here: existing rows have no record of which pool produced them, so they
read as ordinary semantic matches until the next similarity rebuild (scheduled or triggered) writes
the graph again with the flag populated.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '088885cc39b1'
down_revision: Union[str, Sequence[str], None] = 'bfaa6afb4b48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")

    op.add_column(
        "similarity_results",
        sa.Column("matched_reference", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.drop_column("similarity_results", "matched_reference")
