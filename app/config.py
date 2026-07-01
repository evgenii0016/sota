"""Конфигурация приложения из переменных окружения"""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    llm_provider: str = "fake"
    log_level: str = "INFO"
    metrics_enabled: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def _empty_database_url_is_none(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        return str(value)

    @property
    def uses_postgres(self) -> bool:
        return self.database_url is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
