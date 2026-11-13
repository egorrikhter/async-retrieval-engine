from enum import Enum
from functools import lru_cache
from typing import ClassVar

from pydantic import RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class AppEnv(str, Enum):
    LOCAL = "local"
    TEST = "test"
    PROD = "prod"


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore", frozen=True
    )

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    log_level: str = "DEBUG"
    app_env: AppEnv = AppEnv.LOCAL
    debug: bool = True
    redis_port: int = 6379
    redis_db: int = 0
    redis_host: str = "localhost"
    redis_password: SecretStr | None = None
    minio_root_user: SecretStr
    minio_root_password: SecretStr
    minio_endpoint: str = "localhost:9001"
    minio_bucket: str = "documents"
    minio_secure: bool = False

    @property
    def db_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def redis_url(self) -> RedisDsn:
        return RedisDsn.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password.get_secret_value()
            if self.redis_password
            else None,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
