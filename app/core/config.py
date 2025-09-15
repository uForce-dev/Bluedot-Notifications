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

    # RabbitMQ
    rabbitmq_host: str | None = None
    rabbitmq_port: int | None = None
    rabbitmq_user: str | None = None
    rabbitmq_password: str | None = None
    rabbitmq_vhost: str | None = None

    # Google API Service Account
    google_service_account_file: str

    # Mattermost
    mattermost_url: str
    mattermost_token: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def mattermost_domain(self) -> str:
        return (
            settings.mattermost_url.replace("https://", "")
            .replace("http://", "")
            .rstrip("/")
        )

    @property
    def rabbitmq_url(self) -> str | None:
        if not (
            self.rabbitmq_host
            and self.rabbitmq_port
            and self.rabbitmq_user
            and self.rabbitmq_password
        ):
            return None
        vhost = self.rabbitmq_vhost or "%2F"
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/{vhost}"


settings = Settings()  # noqa
