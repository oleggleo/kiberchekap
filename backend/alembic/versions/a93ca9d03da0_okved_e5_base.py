"""ОКВЭД на модель e5-base: размерность вектора 768

Revision ID: a93ca9d03da0
Revises: 7d76911b304c
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a93ca9d03da0"
down_revision: Union[str, None] = "7d76911b304c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_okved_embedding")
    op.execute("TRUNCATE TABLE okved")
    op.execute("ALTER TABLE okved ALTER COLUMN embedding TYPE vector(768)")
    op.execute(
        "CREATE INDEX ix_okved_embedding ON okved "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_okved_embedding")
    op.execute("TRUNCATE TABLE okved")
    op.execute("ALTER TABLE okved ALTER COLUMN embedding TYPE vector(384)")
    op.execute(
        "CREATE INDEX ix_okved_embedding ON okved "
        "USING hnsw (embedding vector_cosine_ops)"
    )
