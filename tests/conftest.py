from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from bookstore.config.database import Base, get_db
from bookstore.main import create_app
from bookstore.models.book import Book  # noqa: F401 — register model metadata


@pytest.fixture(scope="session")
def postgres():
    container = PostgresContainer(image="postgres:15-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def async_engine(postgres):
    host = postgres.get_container_host_ip()
    port = postgres.get_exposed_port(5432)
    user = postgres.username
    password = postgres.password
    dbname = postgres.dbname
    url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
    return create_async_engine(url, echo=False)


@pytest.fixture(scope="session", autouse=True)
async def setup_database(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession]:
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session, session.begin():
        nested = await session.begin_nested()
        yield session
        if nested.is_active:
            await nested.rollback()
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    application = create_app()

    async def override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    application.dependency_overrides.clear()


BOOK_FIXTURE = {
    "title": "Test Book",
    "author": "Test Author",
    "isbn": "9781234567890",
    "publicationYear": 2024,
    "publisher": "Test Publisher",
    "price": 29.99,
    "quantity": 10,
}

BOOK_FIXTURE_2 = {
    "title": "Another Book",
    "author": "Test Author",
    "isbn": "9780987654321",
    "publicationYear": 2023,
    "publisher": "Another Publisher",
    "price": 19.99,
    "quantity": 5,
}
