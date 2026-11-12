from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.src.config.settings import settings


def load_json(name: str) -> Any:
    path = settings.data_dir / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_demo_scenarios() -> list[dict[str, Any]]:
    return load_json("demo_scenarios.json")


def find_demo_scenario(amount_eur: float, currency: str, variation_pct: float, fee_eur: float | None = None) -> dict[str, Any] | None:
    """Busca un escenario determinista de fallback (p.ej. B1)."""
    scenarios = load_demo_scenarios()
    for s in scenarios:
        inp = s.get("inputs", {})
        if (
            float(inp.get("amount_eur", -1)) == float(amount_eur)
            and str(inp.get("quote", "")).upper() == str(currency).upper()
            and float(inp.get("variation_pct", 0)) == float(variation_pct)
        ):
            if fee_eur is None or inp.get("fee_eur") is None or float(inp.get("fee_eur")) == float(fee_eur):
                return s
    return None


def default_fee_for_currency(currency: str) -> float | None:
    try:
        fees = load_json("fee_rules.json")
        for rule in fees:
            corridor = str(rule.get("corridor", ""))
            if corridor.endswith(f"-{currency.upper()}"):
                return float(rule.get("value"))
    except Exception:
        return None
    return None
