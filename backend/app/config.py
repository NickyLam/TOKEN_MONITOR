"""Configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./token_monitor.db"

    # Vendor API keys (optional)
    cursor_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    windsurf_api_key: str = ""

    # App
    debug: bool = False


settings = Settings()
