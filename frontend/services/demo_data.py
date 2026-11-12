def get_demo_response(
    amount_eur: float = 10000,
    fee_eur: float = 40,
    scenario_drop_pct: float = 3
) -> dict:
    """
    Genera resultados ficticios para probar la interfaz
    mientras el backend no está disponible.
    """

    base_rate = 145.0
    net_amount = amount_eur - fee_eur

    stress_rate = base_rate * (1 - scenario_drop_pct / 100)

    base_received = round(net_amount * base_rate)
    stress_received = round(net_amount * stress_rate)

    difference = base_received - stress_received

    budget_total = 1444200
    stress_cov = round((stress_received / budget_total) * 100, 2) if budget_total else 0.0
    budget_gap = max(0, round(budget_total - stress_received, 2))
    budget_impact = {
        "project_id": "KE-HEALTH-001",
        "project_name": "Proyecto Salud Comunitaria — Kenia",
        "currency": "KES",
        "is_synthetic_demo": True,
        "budget_total": budget_total,
        "base_amount_received": base_received,
        "stress_amount_received": stress_received,
        "base_coverage_pct": 100.0 if base_received >= budget_total else round((base_received / budget_total) * 100, 2),
        "stress_coverage_pct": stress_cov,
        "budget_gap": budget_gap,
        "budget_status": "covered" if stress_received >= budget_total else "partial",
    }

    return {
        "reply": (
            f"A transfer of {amount_eur:,.2f} EUR to Kenya would deliver approximately "
            f"{base_received:,.0f} KES under the base scenario (fictional demo reference). "
            f"With an exchange rate decrease of {scenario_drop_pct}%, the estimated amount "
            f"would be {stress_received:,.0f} KES, a potential difference of {difference:,.0f} KES. "
            "This is a local preview estimate, not a backend execution and not a guaranteed quote."
        ),
        "agent": {
            "tools_used": [],
            "reasoning_summary": (
                "Local frontend preview calculated from demo values. No backend tools were executed."
            ),
            "scenarios": [
                {
                    "name": "base",
                    "rate": base_rate,
                    "fee_eur": fee_eur,
                    "amount_received": base_received,
                    "currency": "KES"
                },
                {
                    "name": f"stress_-{scenario_drop_pct}%",
                    "rate": stress_rate,
                    "fee_eur": fee_eur,
                    "amount_received": stress_received,
                    "currency": "KES"
                }
            ],
            "difference": {
                "amount": difference,
                "currency": "KES"
            },
            "budget_impact": budget_impact,
            "assumptions": [
                "Fictional demo reference exchange rate: 145 KES/EUR (preview only).",
                f"Transfer fee: {fee_eur} EUR.",
                f"Stress scenario: {scenario_drop_pct}% exchange rate decrease.",
                "Budget impact shown for synthetic demo project KE-HEALTH-001 (not attributed to specific budget items).",
                "Estimated simulation only; no payment is executed."
            ],
            "alerts": [
                "Local demo preview (frontend): not an AI+tools execution or verified backend result."
            ],
            "execution_mode": "frontend_demo",
            "degraded": True,
            "fx_source": "demo",
            "calculation_source": "frontend_preview"
        }
    }