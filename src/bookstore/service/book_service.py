import math
from uuid import UUID

import structlog
from sqlalchemy import asc, desc, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from bookstore.api.dependencies import PaginationParams
from bookstore.config.retry import db_retry
from bookstore.core.audit import AuditLogger
from bookstore.core.exceptions import NotFoundError, ValidationError
from bookstore.models.book import Book
from bookstore.models.schemas import BookCreate, BookResponse, PageableInfo, PagedBookResponse, SortInfo

logger = structlog.get_logger()


def _author_filter(author: str):
    return Book.author.ilike(func.concat("%", literal(author), "%"))


def _to_response(book: Book) -> BookResponse:
    return BookResponse.model_validate(book)


class BookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @db_retry
    async def get_all(self) -> list[BookResponse]:
        result = await self.db.execute(select(Book).order_by(Book.title))
        books = result.scalars().all()
        return [_to_response(b) for b in books]

    @db_retry
    async def get_by_id(self, book_id: UUID) -> BookResponse:
        book = await self.db.get(Book, book_id)
        if book is None:
            raise NotFoundError("Book", book_id)
        AuditLogger.log_read("Book", book_id)
        return _to_response(book)

    @db_retry
    async def get_by_isbn(self, isbn: str) -> BookResponse:
        result = await self.db.execute(select(Book).where(Book.isbn == isbn))
        book = result.scalar_one_or_none()
        if book is None:
            raise NotFoundError("Book", isbn)
        AuditLogger.log_read("Book", isbn)
        return _to_response(book)

    @db_retry
    async def get_by_author(self, author: str, pagination: PaginationParams) -> PagedBookResponse:
        field_name, direction = pagination.parse_sort()
        column = getattr(Book, field_name)
        order = desc(column) if direction == "desc" else asc(column)

        count_query = select(func.count()).select_from(Book).where(_author_filter(author))
        total_result = await self.db.execute(count_query)
        total_elements = total_result.scalar_one()

        query = select(Book).where(_author_filter(author)).order_by(order).offset(pagination.offset).limit(pagination.size)
        result = await self.db.execute(query)
        books = result.scalars().all()

        total_pages = math.ceil(total_elements / pagination.size) if pagination.size > 0 else 0
        is_sorted = field_name != ""

        sort_info = SortInfo(sorted=is_sorted, unsorted=not is_sorted, empty=not is_sorted)

        return PagedBookResponse(
            content=[_to_response(b) for b in books],
            pageable=PageableInfo(
                pageNumber=pagination.page,
                pageSize=pagination.size,
                sort=sort_info,
                offset=pagination.offset,
            ),
            totalPages=total_pages,
            totalElements=total_elements,
            last=pagination.page >= total_pages - 1,
            size=pagination.size,
            number=pagination.page,
            sort=sort_info,
            numberOfElements=len(books),
            first=pagination.page == 0,
            empty=len(books) == 0,
        )

    @db_retry
    async def create(self, book_data: BookCreate) -> BookResponse:
        existing = await self.db.execute(select(Book).where(Book.isbn == book_data.isbn))
        if existing.scalar_one_or_none() is not None:
            raise ValidationError(f"Book with ISBN '{book_data.isbn}' already exists")

        book = Book(**book_data.model_dump())
        self.db.add(book)
        await self.db.flush()
        await self.db.refresh(book)

        AuditLogger.log_create("Book", book.id, book_data.model_dump())
        logger.info("book_created", book_id=str(book.id), isbn=book.isbn)
        return _to_response(book)

    @db_retry
    async def update(self, book_id: UUID, book_data: BookCreate) -> BookResponse:
        book = await self.db.get(Book, book_id)
        if book is None:
            raise NotFoundError("Book", book_id)

        old_data = BookResponse.model_validate(book).model_dump(mode="json")

        for field, value in book_data.model_dump().items():
            setattr(book, field, value)

        await self.db.flush()
        await self.db.refresh(book)

        new_data = BookResponse.model_validate(book).model_dump(mode="json")
        AuditLogger.log_update("Book", book_id, old_data, new_data)
        logger.info("book_updated", book_id=str(book_id))
        return _to_response(book)

    @db_retry
    async def delete(self, book_id: UUID) -> None:
        book = await self.db.get(Book, book_id)
        if book is None:
            raise NotFoundError("Book", book_id)

        await self.db.delete(book)
        await self.db.flush()
        AuditLogger.log_delete("Book", book_id)
        logger.info("book_deleted", book_id=str(book_id))
