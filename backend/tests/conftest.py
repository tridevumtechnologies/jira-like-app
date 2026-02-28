"""
Shared test fixtures.

Requirements:
  - Postgres test DB at TEST_DATABASE_URL (default: jira_test on localhost)
  - Redis at TEST_REDIS_URL (default: redis://localhost:6379/1)
  - Start infra: docker compose up -d db redis

Isolation strategy
  All tables are emptied (DELETE FROM) after every test via the autouse
  `clean_db` fixture.  This avoids SQLAlchemy 2.0 bind/join-transaction
  complexity while guaranteeing a clean slate for each test.
"""
import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database & redis URLs  (override in CI via env vars)
# ---------------------------------------------------------------------------
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://jira_user:jira_pass@localhost:5432/jira_test",
)
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")

# Patch settings before any call that reads REDIS_URL
import app.core.config as _cfg_module  # noqa: E402
import app.db.redis as _redis_module  # noqa: E402

_cfg_module.settings.REDIS_URL = TEST_REDIS_URL
# Reset the cached Redis singleton so it reconnects to the test DB
_redis_module._redis_client = None

# ---------------------------------------------------------------------------
# Engine (session-scoped — created once per test run)
# ---------------------------------------------------------------------------
test_engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Create / drop all tables once per session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # clean slate
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# ---------------------------------------------------------------------------
# Flush Redis test DB once per session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def flush_test_redis() -> AsyncGenerator[None, None]:
    import redis.asyncio as aioredis

    r = aioredis.from_url(TEST_REDIS_URL)
    await r.flushdb()
    yield
    await r.flushdb()
    await r.aclose()


# ---------------------------------------------------------------------------
# Per-test cleanup — delete all rows after each test (autouse)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def clean_db() -> AsyncGenerator[None, None]:
    yield
    async with TestSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(sa.delete(table))
        await session.commit()


# ---------------------------------------------------------------------------
# Per-test DB session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Per-test HTTP client — overrides get_db with the test session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Registered user fixture
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a user and return the response payload + credentials."""
    payload = {
        "full_name": "Test User",
        "email": "testuser@example.com",
        "password": "Password123",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return {"credentials": payload, "token": resp.json()["access_token"]}


# ---------------------------------------------------------------------------
# Auth headers for the registered user
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def auth_headers(registered_user: dict) -> dict:
    return {"Authorization": f"Bearer {registered_user['token']}"}


# ---------------------------------------------------------------------------
# A project owned by the registered user
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def project(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "key": "TST", "description": "Fixture project"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
