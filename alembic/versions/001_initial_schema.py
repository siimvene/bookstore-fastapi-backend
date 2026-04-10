"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "book",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("isbn", sa.String(length=20), nullable=False),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn", name="uk_book_isbn"),
    )
    op.create_index("idx_book_title", "book", ["title"])
    op.create_index("idx_book_author", "book", ["author"])
    op.create_index("idx_book_isbn", "book", ["isbn"])


def downgrade() -> None:
    op.drop_index("idx_book_isbn", table_name="book")
    op.drop_index("idx_book_author", table_name="book")
    op.drop_index("idx_book_title", table_name="book")
    op.drop_table("book")
