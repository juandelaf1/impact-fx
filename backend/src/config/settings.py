"""Configuración central del backend.

Todas las variables de entorno se leen en un único sitio (este módulo) para
poder validar, documentar y exponer la configuración de forma coherente.
Los valores por defecto son seguros para el modo demo local.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Cargar .env desde la raíz del repo o desde backend/ si existe
BASE_DIR = Path(__file__).resolve().parents[3]  # .../impact-fx
for candidate in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
    if candidate.exists():
        load_dotenv(candidate)
        break
else:
    load_dotenv()


def _env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    """Configuración efectiva del proceso."""

    # --- Aplicación ---------------------------------------------------
    app_name: str = "Impact FX API"
    app_version: str = "0.2.0"
    app_env: str = field(default_factory=lambda: _env_str("APP_ENV", "development"))
    port: int = field(default_factory=lambda: _env_int("PORT", 3001))

    # --- Logging ------------------------------------------------------
    log_level: str = field(default_factory=lambda: _env_str("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: _env_str("LOG_FORMAT", "json"))

    # --- LLM ----------------------------------------------------------
    llm_provider: str = field(default_factory=lambda: _env_str("LLM_PROVIDER", "groq"))
    llm_api_key: str = field(default_factory=lambda: _env_str("LLM_API_KEY"))
    llm_model: str = field(default_factory=lambda: _env_str("LLM_MODEL", "openai/gpt-oss-20b"))
    llm_base_url: str = field(default_factory=lambda: _env_str("LLM_BASE_URL"))
    llm_timeout_seconds: float = field(
        default_factory=lambda: _env_float("LLM_TIMEOUT_SECONDS", 45.0)
    )
    llm_max_retries: int = field(default_factory=lambda: _env_int("LLM_MAX_RETRIES", 2))
    llm_max_history_messages: int = field(
        default_factory=lambda: _env_int("LLM_MAX_HISTORY_MESSAGES", 12)
    )

    # --- API ----------------------------------------------------------
    # Lista de orígenes permitidos separados por coma (demo local por defecto)
    cors_origin: str = field(
        default_factory=lambda: _env_str(
            "CORS_ORIGIN", "http://localhost:8501,http://127.0.0.1:8501"
        )
    )
    rate_limit_enabled: bool = field(default_factory=lambda: _env_bool("RATE_LIMIT_ENABLED", True))
    rate_limit_requests: int = field(default_factory=lambda: _env_int("RATE_LIMIT_REQUESTS", 30))
    rate_limit_window_seconds: int = field(
        default_factory=lambda: _env_int("RATE_LIMIT_WINDOW_SECONDS", 60)
    )
    max_history_messages: int = field(default_factory=lambda: _env_int("MAX_HISTORY_MESSAGES", 20))

    # --- Datos --------------------------------------------------------
    # `demo` (determinista, fixtures) o `live` (Frankfurter con fallback local)
    fx_source: str = field(default_factory=lambda: _env_str("FX_SOURCE", "demo"))
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "processed")

    @property
    def cors_origins(self) -> list[str]:
        """Orígenes CORS effective (nunca vacío)."""

        origins = [o.strip() for o in self.cors_origin.split(",") if o.strip()]
        return origins or ["http://localhost:8501", "http://127.0.0.1:8501"]

    @property
    def is_production(self) -> bool:
        """Indica si el proceso corre en un entorno de producción."""

        return self.app_env.lower() in {"prod", "production"}


settings = Settings()
