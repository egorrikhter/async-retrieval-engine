from fastapi import FastAPI, Request
from sqlalchemy import URL, text

from app.core.database import create_session_factory, get_db_session


async def test_create_session_factory(test_container: URL) -> None:
    async_engine, session_factory = create_session_factory(test_container)
    try:
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await async_engine.dispose()


async def test_get_db_session(test_container: URL) -> None:
    test_app = FastAPI()
    async_engine, session_factory = create_session_factory(test_container)
    test_app.state.session_factory = session_factory
    request = Request(scope={"type": "http", "app": test_app})
    try:
        async for session in get_db_session(request):
            result = await session.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await async_engine.dispose()
