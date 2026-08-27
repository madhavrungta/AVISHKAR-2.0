"""Environment-backed application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils import parse_bounding_box


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Configuration loaded from backend/.env and environment variables."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SIH 26162 Thermal Anomaly API"
    environment: str = "development"
    log_level: str = "INFO"

    firms_map_key: str | None = Field(default=None, repr=False)
    firms_source: str = "VIIRS_SNPP_NRT"
    firms_area: str = "world"
    firms_days: int = 1
    firms_timeout_seconds: float = 30.0
    firms_max_retries: int = 3

    database_url: str = "postgresql+psycopg://sih:sih@localhost:5432/sih26162"
    database_connect_timeout_seconds: int = 3
    raw_data_dir: Path = BACKEND_DIR / "data" / "raw"

    @field_validator("firms_source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("firms_area")
    @classmethod
    def validate_area(cls, value: str) -> str:
        return parse_bounding_box(value)

    @field_validator("firms_days")
    @classmethod
    def validate_days(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("FIRMS_DAYS must be between 1 and 5 for the FIRMS Area API.")
        return value

    @field_validator("firms_timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("FIRMS_TIMEOUT_SECONDS must be greater than zero.")
        return value

    @field_validator("firms_max_retries")
    @classmethod
    def validate_retries(cls, value: int) -> int:
        if not 0 <= value <= 5:
            raise ValueError("FIRMS_MAX_RETRIES must be between 0 and 5.")
        return value

    @field_validator("database_connect_timeout_seconds")
    @classmethod
    def validate_database_timeout(cls, value: int) -> int:
        if not 1 <= value <= 30:
            raise ValueError("DATABASE_CONNECT_TIMEOUT_SECONDS must be between 1 and 30.")
        return value

    @property
    def has_firms_map_key(self) -> bool:
        return bool(self.firms_map_key and self.firms_map_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for the running process."""

    return Settings()
