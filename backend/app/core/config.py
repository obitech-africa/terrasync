
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven TerraSync configuration."""

    PROJECT_NAME: str = "TerraSync API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "demo", "test", "production"] = "development"

    DATABASE_URL: str = "sqlite:///./terrasync.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_SECONDS: int = 30
    DB_POOL_RECYCLE_SECONDS: int = 1800

    CORS_ORIGINS: str = "*"
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = False
    AUTO_MIGRATE_DEVELOPMENT: bool = True

    TRUSTED_PROXY_HEADERS: bool = False
    FORWARDED_ALLOW_IPS: str = "127.0.0.1"
    ENABLE_DOCS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.is_production:
            return self

        if self.is_sqlite:
            raise ValueError(
                "Production DATABASE_URL must use PostgreSQL, not SQLite."
            )

        if self.cors_origins == ["*"]:
            raise ValueError(
                "Production CORS_ORIGINS must explicitly list trusted origins."
            )

        if self.AUTO_MIGRATE_DEVELOPMENT:
            raise ValueError(
                "AUTO_MIGRATE_DEVELOPMENT must be false in production."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
