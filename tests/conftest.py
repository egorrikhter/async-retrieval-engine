from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import httpx
import pytest
from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy import URL
from sqlalchemy.engine import make_url
from testcontainers.community.postgres import PostgresContainer

from app.main import app

alembic_ini_path = Path(__file__).resolve().parents[1] / "alembic.ini"


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


@pytest.fixture(scope="session", autouse=True)
def alembic_config(test_container: URL):
    alembic_cfg = Config(file_=alembic_ini_path)
    alembic_cfg.attributes["url"] = test_container
    upgrade(config=alembic_cfg, revision="head")
