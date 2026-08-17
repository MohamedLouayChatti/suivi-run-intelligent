"""add knowledge base tables

Revision ID: c7e2b91a4d38
Revises: fc4bcdcbdf3b
Create Date: 2026-08-13 14:20:00.000000

The Knowledge Base module's only migration: `similarity_results` is the one table it owns.

An earlier version of this revision also created `knowledge_items`, `ticket_knowledge_items` and
`knowledge_item_identifiers`, with a pgvector `vector` column and an HNSW index over it. That
never ran -- pgvector could not be installed on the machine this project is developed on, and
`CREATE EXTENSION vector` fails outright without it -- so the module's corpus moved to Qdrant
instead of to a Postgres extension. This revision is rewritten rather than followed by a drop
migration because there is nothing in any database to drop.

What stayed behind in Postgres is exactly what is relational rather than vectorial: the derived
similarity graph. Its rows are plain foreign-key-free references to ticket ids, queried by
`source_ticket_id` and ordered by `rank`, with no distance operator anywhere near them. The
knowledge items those edges were computed from live as points in the Qdrant collection, which is
provisioned by `python -m app.scripts.seeding.knowledge_base.backfill --only provision` -- Alembic
has no reach into that store, so its schema is versioned by that pass instead of by this file.

The unique constraint is what makes result generation replaceable rather than append-only: a
source ticket can hold one edge to a given similar ticket, so regenerating a source's results is a
delete-then-insert that cannot silently accumulate duplicates.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c7e2b91a4d38'
down_revision: Union[str, Sequence[str], None] = 'fc4bcdcbdf3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'similarity_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_ticket_id', sa.UUID(), nullable=False),
        sa.Column('similar_ticket_id', sa.UUID(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('embedding_model_version', sa.String(length=50), nullable=False),
        sa.Column('algorithm_version', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'source_ticket_id', 'similar_ticket_id', name='uq_similarity_results_source_similar'
        ),
    )
    # Every read of this table is "the results for this source ticket, in rank order".
    op.create_index(
        'ix_similarity_results_source_ticket_id', 'similarity_results', ['source_ticket_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_similarity_results_source_ticket_id', table_name='similarity_results')
    op.drop_table('similarity_results')
