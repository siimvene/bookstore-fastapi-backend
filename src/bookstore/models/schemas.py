"""Application schemas that extend generated OpenAPI models.

Generated models provide field definitions, constraints, and examples from the
OpenAPI spec (Contract-First). This module adds ORM integration, serializers,
and any application-specific configuration.
"""

from decimal import Decimal
from typing import Any

from pydantic import ConfigDict, field_serializer

from generated.openapi.models import Book as _GeneratedBook
from generated.openapi.models import BookResponse as _GeneratedBookResponse
from generated.openapi.models import PagedBookResponse as _GeneratedPagedBookResponse
from generated.openapi.models import Pageable as _GeneratedPageable
from generated.openapi.models import Problem as _GeneratedProblem
from generated.openapi.models import Sort as _GeneratedSort


class BookCreate(_GeneratedBook):
    """Request model for creating/updating a book. Inherits spec fields.

    Schema title is 'Book' to match the OpenAPI spec component name.
    """

    model_config = ConfigDict(populate_by_name=True, title="Book")


class BookResponse(_GeneratedBookResponse):
    """Response model with ORM support. Inherits spec fields."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_serializer("price")
    @classmethod
    def serialize_price(cls, v: Decimal | float | None) -> float | None:
        return float(v) if v is not None else None


class SortInfo(_GeneratedSort):
    pass


class PageableInfo(_GeneratedPageable):
    model_config = ConfigDict(populate_by_name=True)


class PagedBookResponse(_GeneratedPagedBookResponse):
    """Paginated response with ORM-compatible BookResponse items."""

    model_config = ConfigDict(populate_by_name=True)

    # Override content to use our enriched BookResponse
    content: list[BookResponse] | None = None
    pageable: PageableInfo | None = None
    sort: SortInfo | None = None


class Problem(_GeneratedProblem):
    """RFC 7807 Problem Details. Inherits spec fields."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Problem":
        return cls(**data)
