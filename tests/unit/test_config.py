import os
from pathlib import Path
from typing import TypedDict

import pytest
from pydantic import SecretStr, ValidationError
from pydantic_settings import DotEnvSettingsSource

from app.core.config import AppEnv, Settings


@pytest.fixture(autouse=True)
def clean_app_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key in list(os.environ):
        if key.upper().startswith("APP_"):
            monkeypatch.delenv(key, raising=False)

    monkeypatch.chdir(tmp_path)


def _make_settings(
    *,
    app_env: AppEnv = AppEnv.LOCAL,
    app_debug: bool = False,
    app_postgres_user: str = "postgres_user",
    app_postgres_password: str = "postgres_password",
    app_postgres_db: str = "postgres_db",
    app_minio_root_user: str = "minio_root_user",
    app_minio_root_password: str = "minio_root_password",
    app_postgres_host: str = "postgres_host",
    app_redis_host: str = "redis_host",
    app_minio_host: str = "minio_host",
    app_minio_bucket: str = "minio_bucket",
    db_pool_size: int = 5,
    db_max_overflow: int = 10,
    db_pool_timeout: int = 30,
    db_pool_recycle: int = 1800,
    db_pool_pre_ping: bool = True,
) -> Settings:
    return Settings(
        app_env=app_env,
        app_debug=app_debug,
        app_postgres_user=app_postgres_user,
        app_postgres_password=SecretStr(app_postgres_password),
        app_postgres_db=app_postgres_db,
        app_minio_root_user=app_minio_root_user,
        app_minio_root_password=SecretStr(app_minio_root_password),
        app_postgres_host=app_postgres_host,
        app_redis_host=app_redis_host,
        app_minio_host=app_minio_host,
        app_minio_bucket=app_minio_bucket,
        db_pool_size=db_pool_size,
        db_max_overflow=db_max_overflow,
        db_pool_timeout=db_pool_timeout,
        db_pool_recycle=db_pool_recycle,
        db_pool_pre_ping=db_pool_pre_ping,
    )


class SettingsOverrides(TypedDict, total=False):
    app_env: AppEnv
    app_debug: bool
    app_postgres_user: str
    app_postgres_password: str
    app_postgres_db: str
    app_minio_root_user: str
    app_minio_root_password: str
    app_postgres_host: str
    app_redis_host: str
    app_minio_host: str
    app_minio_bucket: str
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout: int
    db_pool_recycle: int
    db_pool_pre_ping: bool


def test_valid_settings_load() -> None:
    settings = _make_settings()

    assert settings.app_env == AppEnv.LOCAL
    assert settings.db_url.drivername == "postgresql+asyncpg"
    assert settings.db_url.host == settings.app_postgres_host


def test_settings_secrets_masked() -> None:
    settings = _make_settings(app_postgres_password="  secret_password  ")

    assert settings.app_postgres_password.get_secret_value() == "  secret_password  "
    assert "  secret_password  " not in str(settings.db_url)
    assert "  secret_password  " not in repr(settings)


@pytest.mark.parametrize(
    ("overrides", "expected_msg"),
    [
        (
            {"app_env": AppEnv.PROD, "app_debug": True},
            "DEBUG must be False in production.",
        ),
        (
            {
                "app_env": AppEnv.PROD,
                "app_postgres_password": "11charspass",
            },
            "Postgresql password must be at least 12 characters.",
        ),
    ],
)
def test_settings_prod_invariants(
    overrides: SettingsOverrides, expected_msg: str
) -> None:
    with pytest.raises(ValidationError, match=expected_msg):
        _ = _make_settings(**overrides)


@pytest.mark.parametrize(
    ("overrides"),
    [
        ({"app_postgres_user": " "}),
        ({"app_postgres_db": "  "}),
        ({"app_postgres_host": "    "}),
        ({"app_redis_host": "    "}),
        ({"app_minio_root_user": "   "}),
        ({"app_minio_host": ""}),
        ({"app_minio_bucket": ""}),
    ],
)
def test_settings_reject_blank_strings(overrides: SettingsOverrides) -> None:
    with pytest.raises(ValidationError):
        _ = _make_settings(**overrides)


def test_env_example_contract() -> None:
    env_example = Path(__file__).resolve().parents[2] / ".env.example"

    assert env_example.is_file(), f"File not found: {env_example}"

    source = DotEnvSettingsSource(Settings, env_file=env_example)
    env_keys = {key.lower() for key in source.env_vars}
    expected_keys = {name.lower() for name in Settings.model_fields}

    assert env_keys == expected_keys
