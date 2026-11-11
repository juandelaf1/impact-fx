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

    return {
        "reply": (
            f"A transfer of {amount_eur:,.2f} EUR to Kenya "
            f"would deliver approximately {base_received:,.0f} KES "
            f"under the base scenario. With an exchange rate decrease "
            f"of {scenario_drop_pct}%, the estimated amount would be "
            f"{stress_received:,.0f} KES, a difference of "
            f"{difference:,.0f} KES."
        ),
        "agent": {
            "tools_used": [
                "get_fx_reference",
                "calculate_transfer_scenarios"
            ],
            "reasoning_summary": (
                "Demo calculation using a fictional reference exchange rate."
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
            "assumptions": [
                "Fictional reference exchange rate: 145 KES/EUR.",
                f"Transfer fee: {fee_eur} EUR.",
                f"Stress scenario: {scenario_drop_pct}% exchange rate decrease."
            ],
            "alerts": []
        }
    }