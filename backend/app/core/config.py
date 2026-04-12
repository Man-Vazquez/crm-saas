from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, field_validator
from typing import Literal


class Settings(BaseSettings):
    """
    Configuración central de la aplicación.
    
    Pydantic lee automáticamente las variables de entorno
    y las valida contra los tipos definidos aquí.
    Si falta una variable requerida, la app no arranca — falla rápido y claro.
    """

    model_config = SettingsConfigDict(
        env_file=".env",           # busca el archivo .env en la raíz
        env_file_encoding="utf-8",
        case_sensitive=False,      # DATABASE_URL y database_url son lo mismo
        extra="ignore",            # ignora variables del .env que no estén aquí
    )

    # ── Entorno ───────────────────────────────────────────────────────
    # Literal restringe los valores posibles — no puede ser "produccion" con typo
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ── Aplicación ────────────────────────────────────────────────────
    PROJECT_NAME: str = "CRM"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # ── Seguridad ─────────────────────────────────────────────────────
    # str sin default = campo requerido. Si no existe en .env, la app no arranca.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Base de datos ─────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn  # Pydantic valida que sea una URL de Postgres válida

    # ── Redis ─────────────────────────────────────────────────────────
    REDIS_URL: RedisDsn = "redis://redis:6379/0"

    # ── CORS ──────────────────────────────────────────────────────────
    # Lista de orígenes permitidos para el frontend
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]  # puerto de Vite

    @field_validator("DEBUG", mode="before")
    @classmethod
    def set_debug_from_environment(cls, v, info):
        """Debug solo es True en desarrollo, sin importar lo que diga el .env."""
        if info.data.get("ENVIRONMENT") == "production":
            return False
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


# ── Instancia global ──────────────────────────────────────────────────
# Se crea una sola vez al importar el módulo.
# El resto de la app hace: from app.core.config import settings
settings = Settings()