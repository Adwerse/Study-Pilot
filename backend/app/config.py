from typing import Any

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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
