from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_url = settings.DATABASE_URL
_is_sqlite = _url.startswith("sqlite")

engine = create_async_engine(
    _url,
    echo=False,
    # pool_pre_ping not needed for SQLite; connect_args avoids threading issues
    **({} if _is_sqlite else {"pool_pre_ping": True}),
    **({"connect_args": {"check_same_thread": False}} if _is_sqlite else {}),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        yield session
