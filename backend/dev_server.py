"""
Dev server — runs FastAPI without Docker, PostgreSQL, or Redis.

Substitutions:
  - Database : SQLite (file: dev.db in this directory)
  - Redis    : fakeredis (in-memory, no real Redis needed)
  - Tables   : created automatically on startup via SQLAlchemy create_all

Usage:
  # Windows PowerShell
  .\.venv\Scripts\python dev_server.py

  # Or activate the venv first:
  .\.venv\Scripts\Activate.ps1
  python dev_server.py
"""
import os

# ---------------------------------------------------------------------------
# 1. Override env vars BEFORE any app module is imported
#    SQLite URL — file-based so data survives restarts
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")   # unused in dev
os.environ.setdefault("DEV_FAKE_REDIS", "1")                     # use fakeredis
os.environ.setdefault("SECRET_KEY", "dev-only-secret-key-do-not-use-in-production-32x")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://localhost:5173"]')

# ---------------------------------------------------------------------------
# 2. Import the app AFTER env vars are set
# ---------------------------------------------------------------------------
import asyncio

# ---------------------------------------------------------------------------
# 3. Create all tables on startup (replaces running Alembic migrations)
#    Also enables FK enforcement for every SQLite connection (async-safe)
# ---------------------------------------------------------------------------
async def _create_tables() -> None:
    from sqlalchemy import text
    from app.db.session import Base, engine

    async with engine.begin() as conn:
        # Enable FK constraints for SQLite (no-op on other DBs)
        try:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
        except Exception:
            pass
        await conn.run_sync(Base.metadata.create_all)
    print("✓ SQLite tables ready  →  dev.db")

asyncio.run(_create_tables())

# ---------------------------------------------------------------------------
# 4. Start Uvicorn
# ---------------------------------------------------------------------------
import uvicorn

if __name__ == "__main__":
    print("━" * 60)
    print("  Jira-Like API  —  DEV MODE")
    print("  DB    : SQLite (dev.db)")
    print("  Redis : fakeredis (in-memory)")
    print("  Docs  : http://127.0.0.1:8000/docs")
    print("━" * 60)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )
