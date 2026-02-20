"""Database connection and session. Sets app.tenant_id per request for RLS."""
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session(
    tenant_id: UUID | None = None,
    user_id: str | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Get DB session. Sets app.tenant_id for RLS when tenant_id provided."""
    async with async_session_factory() as session:
        if tenant_id:
            await session.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))
        if user_id:
            await session.execute(text(f"SET LOCAL app.user_id = '{user_id}'"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
