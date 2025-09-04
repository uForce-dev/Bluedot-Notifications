from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parent.parent.parent

    # Security
    debug: bool = True
    port: int = 8000

    # Logging
    log_level: str = "DEBUG"

    # Database
    db_scheme: str = "postgresql+psycopg2"
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "postgres"

    # Redis for Celery
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Google API
    google_client_id: str = "YOUR_GOOGLE_CLIENT_ID"
    google_client_secret: str = "YOUR_GOOGLE_CLIENT_SECRET"
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Mattermost
    mattermost_url: str = "YOUR_MATTERMOST_URL"
    mattermost_token: str = "YOUR_MATTERMOST_PERSONAL_ACCESS_TOKEN"
    mattermost_team_name: str = "YOUR_TEAM_NAME"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()
