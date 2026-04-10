from uuid import UUID

from fastapi import APIRouter, Depends, status

from bookstore.api.dependencies import DbSession, PaginationParams
from bookstore.models.schemas import BookCreate, BookResponse, PagedBookResponse, Problem
from bookstore.service.book_service import BookService

router = APIRouter(prefix="/books", tags=["books"])


@router.get(
    "",
    response_model=list[BookResponse],
    summary="List all books",
    description="Returns a list of all books in the Bookstore",
    operation_id="getAllBooks",
)
async def get_all_books(db: DbSession) -> list[BookResponse]:
    service = BookService(db)
    return await service.get_all()


@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new book",
    description="Adds a new book to the Bookstore",
    operation_id="createBook",
    responses={400: {"model": Problem, "content": {"application/problem+json": {}}}},
)
async def create_book(book: BookCreate, db: DbSession) -> BookResponse:
    service = BookService(db)
    return await service.create(book)


@router.get(
    "/isbn/{isbn}",
    response_model=BookResponse,
    summary="Find book by ISBN",
    description="Returns a single book",
    operation_id="getBookByIsbn",
    responses={404: {"model": Problem, "content": {"application/problem+json": {}}}},
)
async def get_book_by_isbn(isbn: str, db: DbSession) -> BookResponse:
    service = BookService(db)
    return await service.get_by_isbn(isbn)


@router.get(
    "/author/{author}",
    response_model=PagedBookResponse,
    summary="Find books by author",
    description="Returns all books by a specific author, or an empty list if none found",
    operation_id="getBooksByAuthor",
)
async def get_books_by_author(
    author: str,
    db: DbSession,
    pagination: PaginationParams = Depends(),
) -> PagedBookResponse:
    service = BookService(db)
    return await service.get_by_author(author, pagination)


@router.get(
    "/{bookId}",
    response_model=BookResponse,
    summary="Get book by ID",
    description="Returns a single book",
    operation_id="getBookById",
    responses={404: {"model": Problem, "content": {"application/problem+json": {}}}},
)
async def get_book_by_id(bookId: UUID, db: DbSession) -> BookResponse:  # noqa: N803
    service = BookService(db)
    return await service.get_by_id(bookId)


@router.put(
    "/{bookId}",
    response_model=BookResponse,
    summary="Update book",
    description="Update an existing book",
    operation_id="updateBook",
    responses={
        400: {"model": Problem, "content": {"application/problem+json": {}}},
        404: {"model": Problem, "content": {"application/problem+json": {}}},
    },
)
async def update_book(bookId: UUID, book: BookCreate, db: DbSession) -> BookResponse:  # noqa: N803
    service = BookService(db)
    return await service.update(bookId, book)


@router.delete(
    "/{bookId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book",
    description="Delete a book from the Bookstore",
    operation_id="deleteBook",
    responses={404: {"model": Problem, "content": {"application/problem+json": {}}}},
)
async def delete_book(bookId: UUID, db: DbSession) -> None:  # noqa: N803
    service = BookService(db)
    await service.delete(bookId)
