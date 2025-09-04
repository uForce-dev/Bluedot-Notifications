from logging.config import dictConfig

from app.core.config import settings


def configure_logging(
    level: str = "INFO", logfile: str = settings.base_dir / "logs/app.log"
) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": level,
                },
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "level": level,
                    "filename": logfile,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": level,
            },
        }
    )
