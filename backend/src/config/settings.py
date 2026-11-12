from __future__ import annotations

import os
from dataclasses import dataclass
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


@dataclass
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    port: int = int(os.getenv("PORT", "3001"))
    # Lista de orígenes permitidos separados por coma (demo local por defecto)
    cors_origin: str = os.getenv("CORS_ORIGIN", "http://localhost:8501,http://127.0.0.1:8501")
    data_dir: Path = BASE_DIR / "data" / "processed"


settings = Settings()
