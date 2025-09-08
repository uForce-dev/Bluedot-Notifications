from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent.parent.parent

    # Security
    debug: bool
    internal_port: int

    # Logging
    log_level: str

    # Timezone
    timezone: str = "UTC"

    # Database
    db_scheme: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    # Redis for Celery
    redis_host: str
    redis_port: int

    # Google API Service Account
    google_service_account_file: str

    # Mattermost
    mattermost_url: str
    mattermost_token: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def mattermost_domain(self) -> str:
        return (
            settings.mattermost_url.replace("https://", "")
            .replace("http://", "")
            .rstrip("/")
        )


settings = Settings()  # noqa
