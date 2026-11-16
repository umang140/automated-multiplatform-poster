from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_channel_username: str | None = None

    discord_webhook_url: str | None = None
    slack_webhook_url: str | None = None

    mastodon_instance_url: str | None = "https://mastodon.social"
    mastodon_access_token: str | None = None

    github_token: str | None = None

    bluesky_handle: str | None = None
    bluesky_app_password: str | None = None
    bluesky_pds_url: str | None = "https://bsky.social"

    hf_token: str | None = None
    hf_repo_id: str | None = None
    hf_repo_type: str | None = "models"

    devto_api_key: str | None = None


def get_settings():
    return Settings()
