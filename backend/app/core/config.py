from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.
    Values are loaded from environment variables / .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Codebase Context Platform"
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Introduced in Step 2, declared now so .env loads cleanly
    DATABASE_URL: str = "sqlite:///./app/data/app.db"

    # Introduced in Step 3
    REPO_STORAGE_PATH: str = "./app/data/repos"

    # Introduced in Step 7
    VECTOR_STORE_PATH: str = "./app/data/vector_store"

    @property
    def repo_storage_dir(self) -> Path:
        """
        Absolute Path to the folder where cloned repositories live.
        Creates the directory (and parents) if it doesn't exist yet.
        """
        path = Path(self.REPO_STORAGE_PATH).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance so we don't re-parse .env on every call.
    """
    return Settings()
