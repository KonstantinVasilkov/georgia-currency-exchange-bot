import os
from pathlib import Path
from sys import modules
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "DEV")

    raw_db_path: str = os.environ.get("DATABASE_URL", "sqlite:///./{}/db.sqlite")
    DATABASE_URL: str = raw_db_path.format(PROJECT_ROOT)
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "123:ABC")
    SENTRY_DSN: str = os.environ.get("SENTRY_DSN", "https://sentry.io/")
    MYFIN_API_BASE_URL: str = os.environ.get(
        "MYFIN_API_BASE_URL", "https://myfin.ge/api/"
    )

    LOG_DIR: Path = PROJECT_ROOT / "logs"
    LOG_FILE: Path = LOG_DIR / "app.log"
    LOG_FORMAT: str = os.environ.get(
        "LOG_FORMAT",
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
    )

    if "pytest" in modules:
        model_config = SettingsConfigDict(
            case_sensitive=True, env_file=f"{PROJECT_ROOT}/.env.test"
        )
    else:
        model_config = SettingsConfigDict(
            case_sensitive=True, env_file=f"{PROJECT_ROOT}/.env.dev"
        )


settings = Settings()
