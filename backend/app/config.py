from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	DATABASE_URL: str
	SECRET_KEY: str
	OPENAI_API_KEY: str
	TENSORIX_API_KEY: str = ""
	TENSORIX_BASE_URL: str = "https://api.tensorix.ai/v1"
	TENSORIX_MODEL: str = "deepseek/deepseek-chat-v3.1"
	BOT_TOKEN: str
	MINI_APP_URL: str
	ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
	DEBUG: bool = False

	model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
