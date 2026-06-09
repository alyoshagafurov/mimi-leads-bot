"""Bot configuration via environment variables (pydantic-settings)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Token from @BotFather (required to run the bot)
    telegram_bot_token: str = ""

    # Local SQLite database file (bot is self-contained by default)
    database_path: str = "bot_leads.db"

    # Optional: read leads from mimi-leads-api instead of the local DB.
    # See "Connecting the bot to the API" in the README.
    api_enabled: bool = False
    api_base_url: str = "http://localhost:8000"

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
