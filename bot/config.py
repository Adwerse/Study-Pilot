from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	BOT_TOKEN: str
	MINI_APP_URL: str
	WEBHOOK_URL: str = ""
	WEBHOOK_PATH: str = "/webhook"
	USE_WEBHOOK: bool = False
	DEBUG: bool = False

	@field_validator("DEBUG", mode="before")
	@classmethod
	def normalize_debug(cls, value: Any) -> Any:
		if isinstance(value, str):
			normalized = value.strip().lower()
			if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
				return True
			if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
				return False

		return value

	model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
