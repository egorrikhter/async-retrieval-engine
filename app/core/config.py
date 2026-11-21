from enum import StrEnum
from functools import lru_cache
from typing import Annotated, ClassVar, Self

from pydantic import (
    BeforeValidator,
    Field,
    SecretStr,
    StringConstraints,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

type CleanStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


def _empty_str_to_none(v: object) -> object:
    return None if v == "" else v


type OptionalSecretStr = Annotated[
    SecretStr | None, BeforeValidator(_empty_str_to_none)
]


def to_upper(value: object) -> object:
    return value.strip().upper() if isinstance(value, str) else value


def to_lower(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


class AppEnv(StrEnum):
    LOCAL = "local"
    PROD = "prod"
    TEST = "test"


class LogLevel(StrEnum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore", frozen=True
    )

    app_postgres_user: CleanStr
    app_postgres_password: Annotated[SecretStr, Field(min_length=1)]
    app_postgres_db: CleanStr
    app_postgres_host: CleanStr = "localhost"

    app_postgres_port: Annotated[int, Field(ge=1, le=65535)] = 5432

    app_log_level: Annotated[
        LogLevel,
        BeforeValidator(to_upper),
    ] = LogLevel.INFO
    app_env: Annotated[AppEnv, BeforeValidator(to_lower)] = AppEnv.LOCAL
    app_debug: bool = False

    app_redis_port: Annotated[int, Field(ge=1, le=65535)] = 6379
    app_redis_db: Annotated[int, Field(ge=0)] = 0
    app_redis_host: CleanStr = "localhost"
    app_redis_password: OptionalSecretStr = None

    app_minio_root_user: CleanStr
    app_minio_root_password: Annotated[SecretStr, Field(min_length=1)]
    app_minio_host: CleanStr = "localhost"
    app_minio_port: Annotated[int, Field(ge=1, le=65535)] = 9000
    app_minio_bucket: CleanStr = "documents"

    @model_validator(mode="after")
    def validate_prod_constraints(self) -> Self:
        if self.app_env == AppEnv.PROD and self.app_debug:
            raise ValueError("DEBUG must be False in production.")
        if (
            self.app_env == AppEnv.PROD
            and len(self.app_postgres_password.get_secret_value()) < 12
        ):
            raise ValueError("Postgresql password must be at least 12 characters.")
        return self

    @property
    def db_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.app_postgres_user,
            password=self.app_postgres_password.get_secret_value(),
            host=self.app_postgres_host,
            port=self.app_postgres_port,
            database=self.app_postgres_db,
        )

    @property
    def minio_endpoint(self) -> str:
        return f"{self.app_minio_host}:{self.app_minio_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings.model_validate({})
