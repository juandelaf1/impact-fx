"""Carga de datos de `data/processed` con caché en memoria.

Los ficheros JSON son la fuente de verdad del MVP: son pequeños y no cambian
en caliente, así que se cachean para no leer disco en cada petición.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from backend.src.config.settings import settings

_CACHE: dict[str, Any] = {}
_CACHE_LOCK = threading.Lock()


def load_json(name: str) -> Any:
    """Carga (y cachea) un JSON de `data/processed`."""

    with _CACHE_LOCK:
        if name in _CACHE:
            return _CACHE[name]

    path: Path = settings.data_dir / name
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    with _CACHE_LOCK:
        _CACHE[name] = data
    return data


def clear_cache() -> None:
    """Vacía la caché de datos (tests / recarga manual)."""

    with _CACHE_LOCK:
        _CACHE.clear()


def load_demo_scenarios() -> list[dict[str, Any]]:
    return load_json("demo_scenarios.json")


def find_demo_scenario(
    amount_eur: float,
    currency: str,
    variation_pct: float,
    fee_eur: float | None = None,
) -> dict[str, Any] | None:
    """Busca un escenario determinista de fallback (p.ej. B1)."""
    scenarios = load_demo_scenarios()
    for s in scenarios:
        inp = s.get("inputs", {})
        if (
            float(inp.get("amount_eur", -1)) == float(amount_eur)
            and str(inp.get("quote", "")).upper() == str(currency).upper()
            and float(inp.get("variation_pct", 0)) == float(variation_pct)
            and (
                fee_eur is None
                or inp.get("fee_eur") is None
                or float(inp.get("fee_eur")) == float(fee_eur)
            )
        ):
            return s
    return None


def default_fee_for_currency(currency: str) -> float | None:
    """Devuelve la comisión por defecto configurada para la moneda destino."""

    try:
        fees = load_json("fee_rules.json")
        for rule in fees:
            corridor = str(rule.get("corridor", ""))
            if corridor.endswith(f"-{currency.upper()}"):
                return float(rule.get("value"))
    except Exception:
        return None
    return None


def supported_corridors() -> list[dict[str, Any]]:
    """Corredores soportados por el MVP,tomados de `corridors.json`.

    La matriz de cobertura vive en los datos (no en el código): añadir un
    corredor es una entrada de datos, no un cambio de lógica.
    """

    try:
        corridors = load_json("corridors.json")
    except Exception:
        return []

    return [
        c
        for c in corridors
        if isinstance(c, dict) and c.get("demo") is True and c.get("origin") == "EUR"
    ]


def find_corridor(destination_country: str, currency: str) -> dict[str, Any] | None:
    """Busca un corredor soportado por país de destino y moneda."""

    dest = str(destination_country or "").strip().upper()
    curr = str(currency or "").strip().upper()
    for corridor in supported_corridors():
        if (
            str(corridor.get("destination_country", "")).upper() == dest
            and str(corridor.get("currency", "")).upper() == curr
        ):
            return corridor
    return None
