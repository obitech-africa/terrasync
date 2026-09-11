import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.db.session import engine_options


def test_production_rejects_sqlite():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///./production.db",
            CORS_ORIGINS="https://ops.example.com",
            AUTO_MIGRATE_DEVELOPMENT=False,
        )


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DATABASE_URL="postgresql://user:password@db:5432/terrasync",
            CORS_ORIGINS="*",
            AUTO_MIGRATE_DEVELOPMENT=False,
        )


def test_valid_production_configuration():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DATABASE_URL="postgresql://user:password@db:5432/terrasync",
        CORS_ORIGINS="https://field.example.com,https://ops.example.com",
        AUTO_MIGRATE_DEVELOPMENT=False,
        ENABLE_DOCS=False,
    )

    assert settings.is_production is True
    assert settings.is_sqlite is False
    assert settings.cors_origins == [
        "https://field.example.com",
        "https://ops.example.com",
    ]


def test_sqlite_engine_options_do_not_apply_queue_pool_settings():
    options = engine_options()

    assert options["pool_pre_ping"] is True
    assert "connect_args" in options
    assert "pool_size" not in options
