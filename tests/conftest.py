from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from sqlalchemy import URL
from sqlalchemy.engine import make_url
from testcontainers.community.postgres import PostgresContainer

from app.main import app


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def test_container() -> Generator[URL, None, None]:
    with PostgresContainer("pgvector/pgvector:pg16") as postgres:
        url = postgres.get_connection_url()
        modified_url = make_url(url).set(drivername="postgresql+asyncpg")
        yield modified_url
