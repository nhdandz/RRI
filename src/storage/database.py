from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    get_settings().DATABASE_URL,
    echo=get_settings().DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def create_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create a new engine + session factory (safe for Celery forked workers)."""
    _engine = create_async_engine(
        get_settings().DATABASE_URL,
        echo=get_settings().DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
