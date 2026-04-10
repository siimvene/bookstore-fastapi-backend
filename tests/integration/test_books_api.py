import pytest
from httpx import AsyncClient

from tests.conftest import BOOK_FIXTURE, BOOK_FIXTURE_2

API_PREFIX = "/api/books"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
class TestBooksApi:
    async def test_get_all_books_empty(self, client: AsyncClient):
        response = await client.get(API_PREFIX)
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_book(self, client: AsyncClient):
        response = await client.post(API_PREFIX, json=BOOK_FIXTURE)
        assert response.status_code == 201

        body = response.json()
        assert body["title"] == BOOK_FIXTURE["title"]
        assert body["author"] == BOOK_FIXTURE["author"]
        assert body["isbn"] == BOOK_FIXTURE["isbn"]
        assert body["id"] is not None
        assert body["createdAt"] is not None
        assert body["updatedAt"] is not None

    async def test_create_book_duplicate_isbn(self, client: AsyncClient):
        await client.post(API_PREFIX, json=BOOK_FIXTURE)
        response = await client.post(API_PREFIX, json=BOOK_FIXTURE)

        assert response.status_code == 400
        body = response.json()
        assert body["status"] == 400
        assert "already exists" in body["detail"]

    async def test_create_book_missing_required_field(self, client: AsyncClient):
        response = await client.post(API_PREFIX, json={"title": "Incomplete"})
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == 400
        assert body["title"] == "Validation Error"

    async def test_get_book_by_id(self, client: AsyncClient):
        create_response = await client.post(API_PREFIX, json=BOOK_FIXTURE)
        book_id = create_response.json()["id"]

        response = await client.get(f"{API_PREFIX}/{book_id}")
        assert response.status_code == 200
        assert response.json()["id"] == book_id

    async def test_get_book_by_id_not_found(self, client: AsyncClient):
        response = await client.get(
            f"{API_PREFIX}/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == 404

    async def test_get_book_by_isbn(self, client: AsyncClient):
        await client.post(API_PREFIX, json=BOOK_FIXTURE)

        response = await client.get(f"{API_PREFIX}/isbn/{BOOK_FIXTURE['isbn']}")
        assert response.status_code == 200
        assert response.json()["isbn"] == BOOK_FIXTURE["isbn"]

    async def test_get_book_by_isbn_not_found(self, client: AsyncClient):
        response = await client.get(f"{API_PREFIX}/isbn/0000000000000")
        assert response.status_code == 404

    async def test_update_book(self, client: AsyncClient):
        create_response = await client.post(API_PREFIX, json=BOOK_FIXTURE)
        book_id = create_response.json()["id"]

        updated = {**BOOK_FIXTURE, "title": "Updated Title", "price": 49.99}
        response = await client.put(f"{API_PREFIX}/{book_id}", json=updated)

        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Updated Title"
        assert body["price"] == 49.99

    async def test_update_book_not_found(self, client: AsyncClient):
        response = await client.put(
            f"{API_PREFIX}/00000000-0000-0000-0000-000000000000",
            json=BOOK_FIXTURE,
        )
        assert response.status_code == 404

    async def test_delete_book(self, client: AsyncClient):
        create_response = await client.post(API_PREFIX, json=BOOK_FIXTURE)
        book_id = create_response.json()["id"]

        response = await client.delete(f"{API_PREFIX}/{book_id}")
        assert response.status_code == 204

        get_response = await client.get(f"{API_PREFIX}/{book_id}")
        assert get_response.status_code == 404

    async def test_delete_book_not_found(self, client: AsyncClient):
        response = await client.delete(
            f"{API_PREFIX}/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_get_books_by_author_paginated(self, client: AsyncClient):
        await client.post(API_PREFIX, json=BOOK_FIXTURE)
        await client.post(API_PREFIX, json=BOOK_FIXTURE_2)

        response = await client.get(
            f"{API_PREFIX}/author/Test Author",
            params={"page": 0, "size": 1, "sort": "title,asc"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["totalElements"] == 2
        assert body["totalPages"] == 2
        assert len(body["content"]) == 1
        assert body["first"] is True
        assert body["last"] is False

    async def test_get_books_by_author_empty(self, client: AsyncClient):
        response = await client.get(f"{API_PREFIX}/author/Nonexistent Author")
        assert response.status_code == 200
        body = response.json()
        assert body["totalElements"] == 0
        assert body["content"] == []
        assert body["empty"] is True

    async def test_health_endpoint(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "UP"}
