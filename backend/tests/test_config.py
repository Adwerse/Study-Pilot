import pytest
from pydantic import ValidationError

from app.config import Settings


def make_production_settings(**overrides):
    values = {
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@db:5432/studypilot",
        "SECRET_KEY": "x" * 40,
        "BOT_TOKEN": "123456:REAL_TELEGRAM_TOKEN",
        "MINI_APP_URL": "https://app.example.com",
        "ALLOWED_ORIGINS": ["https://app.example.com"],
        "OPENAI_API_KEY": "sk-production",
        "TENSORIX_API_KEY": "tensorix-production",
        "INTERNAL_JOBS_SECRET": "internal-jobs-secret",
        "DEBUG": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_settings_accept_safe_required_values():
    settings = make_production_settings()

    assert settings.APP_ENV == "production"
    assert settings.ALLOWED_ORIGINS == ["https://app.example.com"]


def test_production_settings_reject_test_auth():
    with pytest.raises(ValidationError):
        make_production_settings(TEST_AUTH_ENABLED=True)


def test_production_settings_reject_wildcard_cors():
    with pytest.raises(ValidationError):
        make_production_settings(ALLOWED_ORIGINS=["*"])


def test_fake_providers_are_test_only():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LLM_PROVIDER="fake")

    settings = Settings(
        _env_file=None,
        APP_ENV="test",
        TESTING=True,
        LLM_PROVIDER="fake",
        EMBEDDING_PROVIDER="fake",
    )
    assert settings.LLM_PROVIDER == "fake"
    assert settings.EMBEDDING_PROVIDER == "fake"
