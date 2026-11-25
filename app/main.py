from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import create_session_factory
from app.routers.healthcheck import router as healthcheck_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    async_engine, session_factory = create_session_factory(
        settings.db_url,
        settings.db_pool_size,
        settings.db_max_overflow,
        settings.db_pool_timeout,
        settings.db_pool_recycle,
        settings.db_pool_pre_ping,
    )
    app.state.session_factory = session_factory

    try:
        yield

    finally:
        await async_engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(healthcheck_router)
