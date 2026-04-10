from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.config.database import get_db
from bookstore.config.security import get_current_user
from bookstore.core.exceptions import ValidationError

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]

SORTABLE_FIELDS = frozenset(
    {"title", "author", "isbn", "price", "publication_year", "created_at"}
)


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=0, ge=0, description="Page number (zero-based)"),
        size: int = Query(
            default=20, ge=1, le=100, description="Number of records per page"
        ),
        sort: str = Query(
            default="title,asc",
            description="Sort field and direction (e.g. title,asc or price,desc)",
        ),
    ):
        self.page = page
        self.size = size
        self.sort = sort

    @property
    def offset(self) -> int:
        return self.page * self.size

    def parse_sort(self) -> tuple[str, str]:
        parts = self.sort.split(",")
        field = parts[0].strip()
        direction = parts[1].strip().lower() if len(parts) > 1 else "asc"
        if field not in SORTABLE_FIELDS:
            raise ValidationError(
                f"Invalid sort field: {field}. Allowed: {', '.join(sorted(SORTABLE_FIELDS))}"
            )
        return field, direction
