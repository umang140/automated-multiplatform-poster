from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    Missing credentials default to None, which signals individual platform
    adapters to report a 'failed' status with a clear missing-keys error.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot API (requires bot token + target chat id)
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_channel_username: str | None = None

    # Webhook integrations
    discord_webhook_url: str | None = None
    slack_webhook_url: str | None = None

    # Mastodon (Fediverse)
    mastodon_instance_url: str | None = "https://mastodon.social"
    mastodon_access_token: str | None = None

    # GitHub Gists (Personal Access Token with 'gist' scope)
    github_token: str | None = None

    # Bluesky AT Protocol
    bluesky_handle: str | None = None
    bluesky_app_password: str | None = None
    bluesky_pds_url: str | None = "https://bsky.social"

    # Hugging Face (LLM discussions integration)
    hf_token: str | None = None
    hf_repo_id: str | None = None
    hf_repo_type: str | None = "models"

    # Dev.to (Forem API)
    devto_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton to avoid re-reading .env on every request."""
    return Settings()
