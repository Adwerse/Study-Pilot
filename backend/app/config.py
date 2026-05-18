from typing import Any, Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    OPENAI_API_KEY: str
    TENSORIX_API_KEY: str = ""
    TENSORIX_BASE_URL: str = "https://api.tensorix.ai/v1"
    TENSORIX_MODEL: str = "deepseek/deepseek-chat-v3.1"
    BOT_TOKEN: str = Field(
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")
    )
    MINI_APP_URL: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    DEBUG: bool = False
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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
