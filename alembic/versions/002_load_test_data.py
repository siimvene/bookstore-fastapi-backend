"""Load test data

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO book (id, title, author, isbn, publication_year, publisher, price, quantity)
        VALUES
          ('cfa5fde1-ad43-4463-9b14-8580f3fe04a8', 'Spring Boot in Action', 'Craig Walls', '9781617292545', 2016, 'Manning Publications', 39.99, 25),
          ('f0f7d4c8-9bce-43fa-b707-8b5d10f0b92a', 'Clean Code', 'Robert C. Martin', '9780132350884', 2008, 'Prentice Hall', 44.99, 15),
          ('a9b8c7d6-e5f4-3210-9876-5432a1b0c9d8', 'Effective Java', 'Joshua Bloch', '9780134685991', 2018, 'Addison-Wesley', 49.99, 10)
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM book WHERE id IN (
            'cfa5fde1-ad43-4463-9b14-8580f3fe04a8',
            'f0f7d4c8-9bce-43fa-b707-8b5d10f0b92a',
            'a9b8c7d6-e5f4-3210-9876-5432a1b0c9d8'
        )
    """)
