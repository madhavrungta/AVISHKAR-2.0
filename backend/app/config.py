import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

logger = logging.getLogger("firms_app.config")

class Settings(BaseSettings):
    # NASA FIRMS API settings
    FIRMS_MAP_KEY: str = ""
    FIRMS_SOURCE: str = "VIIRS_SNPP_NRT"
    FIRMS_AREA: str = "68.0,6.0,97.0,37.0"  # West, South, East, North (default: India region)
    FIRMS_DAYS: int = 1
    FIRMS_BASE_URL: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    ASSOCIATION_RADIUS_METERS: float = 3000.0

    # Nominatim Enrichment settings
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"

    # Database configuration
    DATABASE_URL: str = "sqlite:///./thermal_observations.db"
    POSTGRES_USER: str = "firms_user"
    POSTGRES_PASSWORD: str = "firms_password"
    POSTGRES_DB: str = "firms_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Application settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    # ML Classifier Shadow Mode Feature Flag (Safe default: False)
    ML_CLASSIFIER_SHADOW_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_firms_key_configured(self) -> bool:
        key = self.FIRMS_MAP_KEY.strip()
        return bool(key and key != "your_key_here" and key != "YOUR_MAP_KEY")

    def get_firms_key_safety_status(self) -> dict:
        if self.is_firms_key_configured:
            masked_key = self.FIRMS_MAP_KEY[:4] + "..." + self.FIRMS_MAP_KEY[-4:] if len(self.FIRMS_MAP_KEY) > 8 else "***"
            return {
                "configured": True,
                "message": f"FIRMS_MAP_KEY is active ({masked_key})."
            }
        else:
            return {
                "configured": False,
                "message": "FIRMS_MAP_KEY is not configured. Add it to backend/.env."
            }

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
