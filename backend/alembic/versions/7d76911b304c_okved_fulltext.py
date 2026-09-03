"""Полнотекстовый индекс по названиям ОКВЭД

Revision ID: 7d76911b304c
Revises: c069bf17f6a8
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op

revision: str = "7d76911b304c"
down_revision: Union[str, None] = "c069bf17f6a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_okved_name_fts ON okved "
        "USING gin (to_tsvector('russian', name))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_okved_name_fts")
