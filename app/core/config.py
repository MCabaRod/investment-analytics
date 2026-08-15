"""
Configuración centralizada de la aplicación.

Todas las opciones se leen de variables de entorno (nunca hardcodear secretos
ni credenciales). Ver `.env.example` para la lista completa de variables.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    app_name: str = "Investment Analytics"
    environment: str = Field(default="development")  # development | staging | production
    debug: bool = Field(default=True)

    # --- Seguridad ---
    secret_key: str = Field(default="CHANGE_ME_INSECURE_DEFAULT")
    access_token_expire_minutes: int = Field(default=60 * 24)
    algorithm: str = Field(default="HS256")

    # --- Base de datos ---
    database_url: str = Field(
        default="postgresql+psycopg://investuser:investpass@db:5432/investment_analytics"
    )
    database_echo: bool = Field(default=False)

    # --- CORS ---
    cors_allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:8000"])

    # --- Proveedores de datos ---
    alpha_vantage_api_key: str | None = Field(default=None)
    twelve_data_api_key: str | None = Field(default=None)

    # --- Tareas programadas ---
    update_interval_minutes: int = Field(default=60)
    enable_scheduler: bool = Field(default=True)

    # --- Cálculos financieros ---
    risk_free_rate: float = Field(
        default=0.02,
        description="Tasa libre de riesgo anual usada en Sharpe/Sortino. Configurable y documentada, nunca asumida arbitrariamente en el código de cálculo.",
    )


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración cacheada (una sola lectura de entorno por proceso)."""
    return Settings()
