import logging
from logging.config import dictConfig
from logging.handlers import TimedRotatingFileHandler  # noqa: F401  (referenced via dictConfig)
from contextvars import ContextVar

from app.core.config import settings


request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = request_id_var.get()
        except Exception:
            record.request_id = "-"
        return True


def configure_logging(
    level: str = "INFO", logfile: str = settings.base_dir / "logs/app.log"
) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": "app.core.RequestIdFilter",
                }
            },
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] [rid=%(request_id)s] %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": level,
                    "filters": ["request_id"],
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "when": "midnight",
                    "backupCount": 14,
                    "formatter": "default",
                    "level": level,
                    "filename": str(logfile),
                    "encoding": "utf-8",
                    "filters": ["request_id"],
                },
            },
            "loggers": {
                "uvicorn.error": {"level": level},
                "uvicorn.access": {"level": level},
                "celery": {"level": level},
            },
            "root": {"handlers": ["console", "file"], "level": level},
        }
    )
