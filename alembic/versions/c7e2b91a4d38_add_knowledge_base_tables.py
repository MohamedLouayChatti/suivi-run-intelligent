"""add knowledge base tables

Revision ID: c7e2b91a4d38
Revises: fc4bcdcbdf3b
Create Date: 2026-08-13 14:20:00.000000

The Knowledge Base module's first migration -- none of its tables existed in the schema before
this, which is why they are all created together here.

`knowledge_items` is the base of a joined-table inheritance hierarchy discriminated by
`source_type`; `ticket_knowledge_items` is its first subtype and application documentation will
be the second. The vector column stays on the base table so the eventual ANN index covers every
source with one index.

The embedding column is deliberately left dimensionless (`vector` rather than `vector(n)`):
no embedding model has been chosen yet, and pinning the dimension plus adding the real
HNSW/IVFFlat index is a follow-up migration once the evaluation picks a winner.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'c7e2b91a4d38'
down_revision: Union[str, Sequence[str], None] = 'fc4bcdcbdf3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    knowledge_source_type = postgresql.ENUM('TICKET', name='knowledge_source_type')
    knowledge_identifier_type = postgresql.ENUM(
        'INCIDENT_REF', 'ORDER_REF', 'PRESTATION_REF', 'TRANSFER_ID', 'JOB_RUN_ID',
        'USER_CUID', 'SITE_CODE', 'BUILDING_CODE', 'LINK_CODE',
        name='knowledge_identifier_type',
    )
    knowledge_source_type.create(op.get_bind())
    knowledge_identifier_type.create(op.get_bind())

    op.create_table(
        'knowledge_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_type', knowledge_source_type, nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        # Reuses Ticket Management's existing native enum type rather than declaring a duplicate.
        sa.Column(
            'application',
            postgresql.ENUM('FCI', 'COLORIS', 'AERO', 'VIO', name='ticket_application', create_type=False),
            nullable=False,
        ),
        sa.Column('embedding', Vector(), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('embedding_model_version', sa.String(length=50), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_items_source_id', 'knowledge_items', ['source_id'], unique=False)
    op.create_index('ix_knowledge_items_application', 'knowledge_items', ['application'], unique=False)

    op.create_table(
        'ticket_knowledge_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('genergy_id', sa.String(length=50), nullable=True),
        sa.Column('oceane_id', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['knowledge_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    # Indexed because it is the right-hand side of every reference lookup: a description citing
    # "INC001010948992" resolves against this column, not against other descriptions.
    op.create_index(
        'ix_ticket_knowledge_items_genergy_id', 'ticket_knowledge_items', ['genergy_id'], unique=False
    )

    op.create_table(
        'knowledge_item_identifiers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('knowledge_item_id', sa.UUID(), nullable=False),
        sa.Column('identifier_type', knowledge_identifier_type, nullable=False),
        sa.Column('value', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['knowledge_item_id'], ['knowledge_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_knowledge_item_identifiers_value_type',
        'knowledge_item_identifiers', ['value', 'identifier_type'], unique=False,
    )
    op.create_index(
        'ix_knowledge_item_identifiers_item_id',
        'knowledge_item_identifiers', ['knowledge_item_id'], unique=False,
    )

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
    op.create_index(
        'ix_similarity_results_source_ticket_id', 'similarity_results', ['source_ticket_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_similarity_results_source_ticket_id', table_name='similarity_results')
    op.drop_table('similarity_results')

    op.drop_index('ix_knowledge_item_identifiers_item_id', table_name='knowledge_item_identifiers')
    op.drop_index('ix_knowledge_item_identifiers_value_type', table_name='knowledge_item_identifiers')
    op.drop_table('knowledge_item_identifiers')

    op.drop_index('ix_ticket_knowledge_items_genergy_id', table_name='ticket_knowledge_items')
    op.drop_table('ticket_knowledge_items')

    op.drop_index('ix_knowledge_items_application', table_name='knowledge_items')
    op.drop_index('ix_knowledge_items_source_id', table_name='knowledge_items')
    op.drop_table('knowledge_items')

    postgresql.ENUM(name='knowledge_identifier_type').drop(op.get_bind())
    postgresql.ENUM(name='knowledge_source_type').drop(op.get_bind())

    # The `vector` extension is left in place: dropping it would break any other object that
    # comes to depend on it, and re-creating it is idempotent.
