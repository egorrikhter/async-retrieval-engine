from collections.abc import AsyncGenerator
from typing import cast

from fastapi import Request
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_session_factory(
    url: URL,
    db_pool_size: int = 5,
    db_max_overflow: int = 10,
    db_pool_timeout: int = 30,
    db_pool_recycle: int = 1800,
    db_pool_pre_ping: bool = True,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    async_engine = create_async_engine(
        url=url,
        pool_size=db_pool_size,
        max_overflow=db_max_overflow,
        pool_timeout=db_pool_timeout,
        pool_recycle=db_pool_recycle,
        pool_pre_ping=db_pool_pre_ping,
    )

    sessionmaker = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_engine, sessionmaker


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory = cast(
        async_sessionmaker[AsyncSession], request.app.state.session_factory
    )

    async with session_factory() as session:
        yield session
