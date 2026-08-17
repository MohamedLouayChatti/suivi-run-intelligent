"""pin embedding dimension and add hnsw index

Revision ID: a4f61c8b7e05
Revises: c7e2b91a4d38
Create Date: 2026-08-14 10:00:00.000000

The follow-up migration c7e2b91a4d38 deliberately left open: it created `knowledge_items.embedding`
as a dimensionless `vector` because no embedding model had been chosen, and pgvector cannot build an
ANN index over a column of unknown width.

The evaluation (notebooks/models_evaluation/) picked bge-m3, which emits 1024-dimensional vectors,
so the column is pinned to `vector(1024)` and the real index is created here.

HNSW rather than IVFFlat: IVFFlat must be built against an already-populated table and re-tuned as
the corpus grows, whereas HNSW is built incrementally and needs no such maintenance -- the right
trade for a table that is populated once by backfill and then grows one ticket at a time.
`vector_cosine_ops` matches the operator the search port actually queries with (`<=>`); an index
built for a different metric would simply never be used. m=16 / ef_construction=64 are pgvector's
defaults, written out explicitly so re-running this reproduces the same index.

Known limitation, deliberately not solved here: every vector query in this module is filtered
(`WHERE application = :app`), and a plain HNSW scan can under-return under a filter because it
picks its `ef_search` candidates before the filter is applied. At the current corpus size the
planner chooses an exact scan anyway, so it cannot bite yet. When it does, the two options are
pgvector 0.8's `hnsw.iterative_scan`, or one partial HNSW index per Application -- both are
changes to how the index is queried or partitioned, not to the choice of HNSW.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a4f61c8b7e05'
down_revision: Union[str, Sequence[str], None] = 'c7e2b91a4d38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 1024
HNSW_INDEX_NAME = 'ix_knowledge_items_embedding_hnsw'


def upgrade() -> None:
    """Upgrade schema."""
    # USING is required: Postgres will not implicitly widen `vector` to `vector(n)`, since it has
    # to verify every existing row actually has n dimensions.
    op.execute(
        f'ALTER TABLE knowledge_items '
        f'ALTER COLUMN embedding TYPE vector({EMBEDDING_DIMENSIONS}) '
        f'USING embedding::vector({EMBEDDING_DIMENSIONS})'
    )
    op.execute(
        f'CREATE INDEX {HNSW_INDEX_NAME} ON knowledge_items '
        f'USING hnsw (embedding vector_cosine_ops) '
        f'WITH (m = 16, ef_construction = 64)'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f'DROP INDEX IF EXISTS {HNSW_INDEX_NAME}')
    # Back to an unconstrained `vector`. Widening is lossless -- every row keeps the exact vector
    # it held -- so this is a genuine inverse, not a data-destroying downgrade.
    op.execute('ALTER TABLE knowledge_items ALTER COLUMN embedding TYPE vector USING embedding::vector')
