from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from bookstore.api.dependencies import PaginationParams
from bookstore.core.exceptions import NotFoundError, ValidationError
from bookstore.models.book import Book
from bookstore.service.book_service import BookService


def _make_book(**overrides):
    from datetime import datetime

    defaults = {
        "id": uuid4(),
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "9781234567890",
        "publication_year": 2024,
        "publisher": "Test Publisher",
        "price": 29.99,
        "quantity": 10,
        "created_at": datetime.now(tz=UTC),
        "updated_at": datetime.now(tz=UTC),
    }
    defaults.update(overrides)
    book = Book()
    for k, v in defaults.items():
        setattr(book, k, v)
    return book


@pytest.mark.unit
class TestBookService:
    @pytest.fixture
    def db_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, db_session):
        return BookService(db_session)

    async def test_get_all_returns_books(self, service, db_session):
        book = _make_book()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [book]
        db_session.execute.return_value = result_mock

        result = await service.get_all()

        assert len(result) == 1
        assert result[0].title == book.title

    async def test_get_by_id_returns_book(self, service, db_session):
        book = _make_book()
        db_session.get.return_value = book

        result = await service.get_by_id(book.id)

        assert result.id == book.id
        db_session.get.assert_called_once_with(Book, book.id)

    async def test_get_by_id_not_found_raises(self, service, db_session):
        db_session.get.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id(uuid4())

    async def test_get_by_isbn_returns_book(self, service, db_session):
        book = _make_book()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = book
        db_session.execute.return_value = result_mock

        result = await service.get_by_isbn(book.isbn)

        assert result.isbn == book.isbn

    async def test_get_by_isbn_not_found_raises(self, service, db_session):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db_session.execute.return_value = result_mock

        with pytest.raises(NotFoundError):
            await service.get_by_isbn("0000000000000")

    @patch("bookstore.service.book_service.AuditLogger")
    async def test_create_book(self, mock_audit, service, db_session):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db_session.execute.return_value = result_mock

        from datetime import datetime

        from bookstore.models.schemas import BookCreate

        book_data = BookCreate(
            title="New Book",
            author="Author",
            isbn="9999999999999",
        )

        async def fake_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime.now(tz=UTC)
            obj.updated_at = datetime.now(tz=UTC)

        db_session.refresh = fake_refresh

        result = await service.create(book_data)

        assert result.title == "New Book"
        db_session.add.assert_called_once()

    async def test_create_book_duplicate_isbn_raises(self, service, db_session):
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = _make_book()
        db_session.execute.return_value = result_mock

        from bookstore.models.schemas import BookCreate

        book_data = BookCreate(title="Dup", author="Author", isbn="9781234567890")

        with pytest.raises(ValidationError, match="already exists"):
            await service.create(book_data)

    async def test_delete_not_found_raises(self, service, db_session):
        db_session.get.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete(uuid4())

    def test_parse_sort_invalid_field_raises(self):
        pagination = PaginationParams()
        pagination.sort = "invalid_field,asc"

        with pytest.raises(ValidationError, match="Invalid sort field"):
            pagination.parse_sort()
