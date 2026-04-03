from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralise la configuration backend lue depuis `.env`.

    Les paramètres ajoutés ici servent à piloter le quota, le stockage temporaire
    des documents importés et les valeurs système utilisées par les services métier.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CESOC Print System API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/cesoc_print_system",
        alias="DATABASE_URL",
    )
    cors_origins: str = "http://localhost,http://127.0.0.1"
    default_daily_quota: int = 10
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    imported_documents_path: str = "storage/imported_documents"
    max_pdf_size_mb: int = 25
    print_job_retention_days: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
