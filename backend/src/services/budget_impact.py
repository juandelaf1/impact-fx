from __future__ import annotations

from typing import Any


def calculate_budget_impact(
    base_amount_received: float,
    stressed_amount_received: float,
    project_budget: dict[str, Any],
) -> dict[str, Any]:
    """Calcula cobertura y brecha presupuestaria de forma determinista.

    No asigna déficit a partidas concretas.
    """
    items = project_budget.get("items") or []
    total = 0.0
    for item in items:
        try:
            total += float(item.get("amount_local", 0) or 0)
        except Exception:
            continue

    base_received = float(base_amount_received or 0)
    stress_received = float(stressed_amount_received or 0)

    def pct(received: float) -> float:
        if total <= 0:
            return 0.0
        return round((received / total) * 100, 2)

    base_cov = pct(base_received)
    stress_cov = pct(stress_received)
    gap = max(0.0, round(total - stress_received, 2))

    if stress_received >= total:
        status = "covered"
    elif stress_received > 0:
        status = "partial"
    else:
        status = "uncovered"

    return {
        "project_id": project_budget.get("project_id"),
        "project_name": project_budget.get("name"),
        "currency": project_budget.get("currency"),
        "is_synthetic_demo": True,
        "budget_total": round(total, 2),
        "base_amount_received": round(base_received, 2),
        "stress_amount_received": round(stress_received, 2),
        "base_coverage_pct": base_cov,
        "stress_coverage_pct": stress_cov,
        "budget_gap": gap,
        "budget_status": status,
    }
