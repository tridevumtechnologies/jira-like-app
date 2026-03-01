"""
Shared test fixtures — no real database or Redis required.

Strategy
  - SQLite in-memory  (via aiosqlite) replaces PostgreSQL
  - fakeredis         replaces Redis
  Tables are recreated once per session; all rows DELETEd after each test.
"""
import os

# ── Must be set BEFORE any app import so settings & redis module pick them up ──
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")   # unused but required by Settings
os.environ["DEV_FAKE_REDIS"] = "1"

from typing import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# In-memory SQLite engine (session-scoped)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Create / drop all tables once per test session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


# ---------------------------------------------------------------------------
# Flush fakeredis once per session (no-op: fakeredis is already empty)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def flush_test_redis() -> AsyncGenerator[None, None]:
    import app.db.redis as _redis_module  # noqa: E402

    _redis_module._redis_client = None   # force re-init as fakeredis
    yield
    if _redis_module._redis_client is not None:
        await _redis_module._redis_client.flushdb()
        await _redis_module._redis_client.aclose()
    _redis_module._redis_client = None


# ---------------------------------------------------------------------------
# Per-test cleanup — wipe all rows after each test
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def clean_db() -> AsyncGenerator[None, None]:
    yield
    async with TestSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(sa.delete(table))
        await session.commit()

    # Also reset the fakeredis client so tokens don't leak between tests
    import app.db.redis as _redis_module  # noqa: E402
    if _redis_module._redis_client is not None:
        await _redis_module._redis_client.flushdb()


# ---------------------------------------------------------------------------
# Per-test DB session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Per-test HTTP client — injects the SQLite test session into the app
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
