from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	BOT_TOKEN: str
	MINI_APP_URL: str
	WEBHOOK_URL: str = ""
	WEBHOOK_PATH: str = "/webhook"
	USE_WEBHOOK: bool = False
	DEBUG: bool = False

	model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
