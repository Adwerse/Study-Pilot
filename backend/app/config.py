import json
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["development", "test", "staging", "production"]
LLMProvider = Literal["tensorix", "openai", "fake"]
EmbeddingProvider = Literal["openai", "fake"]


class Settings(BaseSettings):
    APP_ENV: Environment = "development"
    TESTING: bool = False
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/learning_os"
    )
    SECRET_KEY: str = "dev-secret-key-change-me"
    OPENAI_API_KEY: str = ""
    LLM_PROVIDER: LLMProvider = "tensorix"
    EMBEDDING_PROVIDER: EmbeddingProvider = "openai"
    TENSORIX_API_KEY: str = ""
    TENSORIX_BASE_URL: str = "https://api.tensorix.ai/v1"
    TENSORIX_MODEL: str = "deepseek/deepseek-chat-v3.1"
    BOT_TOKEN: str = Field(
        default="", validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")
    )
    MINI_APP_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    DEBUG: bool = False
    TEST_AUTH_ENABLED: bool = False
    TEST_AUTH_SECRET: str = "studypilot-test-secret"
    E2E_TEST_SECRET: str = "studypilot-e2e-secret"
    INTERNAL_JOBS_SECRET: str = ""
    NOTIFICATIONS_ENABLED: bool = True
    NOTIFICATIONS_POLL_INTERVAL_SECONDS: int = 30
    DOCUMENT_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    DOCUMENT_CHUNK_SIZE_CHARS: int = 1600
    DOCUMENT_CHUNK_OVERLAP_CHARS: int = 200
    DOCUMENT_MAX_CHUNKS: int = 500
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    VECTOR_STORE_PROVIDER: Literal["pgvector", "qdrant"] = "pgvector"
    VECTOR_SEARCH_TOP_K_DEFAULT: int = 8
    VECTOR_SEARCH_SCORE_THRESHOLD: float = 0.2
    RAG_REWRITE_MODEL: str = "deepseek/deepseek-chat-v3.1"
    RAG_ANSWER_MODEL: str = "deepseek/deepseek-chat-v3.1"
    RAG_TOP_K_DEFAULT: int = 8
    RAG_RERANK_TOP_K_DEFAULT: int = 4
    RAG_MIN_SCORE_THRESHOLD: float = 0.2
    RAG_MAX_CONTEXT_CHARS: int = 12000
    RAG_SNIPPET_CHARS: int = 300
    ANALYTICS_AI_ENABLED: bool = True
    ANALYTICS_MODEL: str = ""
    WEEKLY_REVIEW_AI_ENABLED: bool = True
    WEEKLY_REVIEW_MODEL: str = ""
    WEEKLY_DIGEST_ENABLED: bool = True
    WEEKLY_DIGEST_DAY: int = 6
    WEEKLY_DIGEST_HOUR: int = 18
    WEEKLY_DIGEST_POLL_INTERVAL_SECONDS: int = 900
    WEEKLY_DIGEST_BATCH_LIMIT: int = 100

    @property
    def telegram_bot_token(self) -> str:
        return self.BOT_TOKEN

    @property
    def is_test_environment(self) -> bool:
        return self.APP_ENV == "test" and self.TESTING

    @property
    def is_test_auth_enabled(self) -> bool:
        return self.is_test_environment and self.TEST_AUTH_ENABLED

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {
                "0",
                "false",
                "no",
                "off",
                "release",
                "prod",
                "production",
            }:
                return False

        return value

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def normalize_app_env(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            aliases = {
                "dev": "development",
                "local": "development",
                "prod": "production",
                "ci": "test",
                "testing": "test",
            }
            return aliases.get(normalized, normalized)
        return value

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper() or "INFO"
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return parsed
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator("WEEKLY_DIGEST_DAY", mode="before")
    @classmethod
    def normalize_weekly_digest_day(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            days = {
                "monday": 0,
                "mon": 0,
                "tuesday": 1,
                "tue": 1,
                "wednesday": 2,
                "wed": 2,
                "thursday": 3,
                "thu": 3,
                "friday": 4,
                "fri": 4,
                "saturday": 5,
                "sat": 5,
                "sunday": 6,
                "sun": 6,
            }
            return days.get(normalized, value)
        return value

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> "Settings":
        if self.APP_ENV == "production":
            self._validate_production_settings()
        if self.TEST_AUTH_ENABLED and not self.is_test_environment:
            raise ValueError("TEST_AUTH_ENABLED requires APP_ENV=test and TESTING=true")
        if self.LLM_PROVIDER == "fake" and not self.is_test_environment:
            raise ValueError("LLM_PROVIDER=fake is only allowed in test")
        if self.EMBEDDING_PROVIDER == "fake" and not self.is_test_environment:
            raise ValueError("EMBEDDING_PROVIDER=fake is only allowed in test")
        return self

    def _validate_production_settings(self) -> None:
        required_values = {
            "DATABASE_URL": self.DATABASE_URL,
            "SECRET_KEY": self.SECRET_KEY,
            "BOT_TOKEN/TELEGRAM_BOT_TOKEN": self.BOT_TOKEN,
            "MINI_APP_URL": self.MINI_APP_URL,
            "VECTOR_STORE_PROVIDER": self.VECTOR_STORE_PROVIDER,
            "EMBEDDING_MODEL": self.EMBEDDING_MODEL,
            "INTERNAL_JOBS_SECRET": self.INTERNAL_JOBS_SECRET,
        }
        missing = [
            name for name, value in required_values.items() if not str(value).strip()
        ]
        if missing:
            raise ValueError(
                f"Missing required production settings: {', '.join(missing)}"
            )

        if self.SECRET_KEY == "dev-secret-key-change-me" or len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be a strong production secret")
        if self.BOT_TOKEN in {"", "123456:TEST_TOKEN", "your-telegram-bot-token"}:
            raise ValueError("BOT_TOKEN must be a real production Telegram bot token")
        if self.TESTING or self.TEST_AUTH_ENABLED:
            raise ValueError(
                "TESTING and TEST_AUTH_ENABLED must be disabled in production"
            )
        if self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if not self.ALLOWED_ORIGINS:
            raise ValueError("ALLOWED_ORIGINS must be set in production")
        if "*" in self.ALLOWED_ORIGINS:
            raise ValueError("ALLOWED_ORIGINS cannot include '*' in production")
        for origin in self.ALLOWED_ORIGINS:
            parsed = urlparse(origin)
            if parsed.scheme != "https":
                raise ValueError("ALLOWED_ORIGINS must use https in production")
            if parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
                raise ValueError(
                    "ALLOWED_ORIGINS cannot include local hosts in production"
                )
        if self.MINI_APP_URL.startswith("http://"):
            raise ValueError("MINI_APP_URL must use https in production")
        if self.LLM_PROVIDER == "tensorix" and not self.TENSORIX_API_KEY:
            raise ValueError("TENSORIX_API_KEY is required when LLM_PROVIDER=tensorix")
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.EMBEDDING_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
            )
        if self.EMBEDDING_DIMENSIONS <= 0:
            raise ValueError("EMBEDDING_DIMENSIONS must be positive")

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", populate_by_name=True
    )


settings = Settings()
