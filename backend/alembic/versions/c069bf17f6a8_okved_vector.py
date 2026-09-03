"""ОКВЭД: расширение vector, справочник и поля в лидах

Revision ID: c069bf17f6a8
Revises: 775df98f1fd0
Create Date: 2026-09-02

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision: str = "c069bf17f6a8"
down_revision: Union[str, None] = "775df98f1fd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "okved",
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("name", sa.String(length=400), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(384), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.execute(
        "CREATE INDEX ix_okved_embedding ON okved "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    op.add_column("leads", sa.Column("okved_code", sa.String(length=12), nullable=True))
    op.add_column("leads", sa.Column("okved_name", sa.String(length=400), nullable=True))
    op.add_column("leads", sa.Column("okved_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "okved_score")
    op.drop_column("leads", "okved_name")
    op.drop_column("leads", "okved_code")
    op.execute("DROP INDEX IF EXISTS ix_okved_embedding")
    op.drop_table("okved")
