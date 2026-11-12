from __future__ import annotations

import argparse
import os
import sys

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:3001").rstrip("/")
TIMEOUT = 90
EXPECTED_BASE = 1444200
EXPECTED_STRESS = 1400874
EXPECTED_DIFFERENCE = 43326
EXPECTED_TOOLS = {"get_fx_reference", "calculate_transfer_scenarios"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Expect deterministic backend fallback because the LLM is unavailable.",
    )
    args = parser.parse_args()
    failures: list[str] = []

    try:
        health = requests.get(f"{API_BASE_URL}/api/health", timeout=10)
    except requests.RequestException as exc:
        print(f"[FAIL] backend health request: {exc}")
        return 1
    if health.status_code != 200 or health.json().get("status") != "ok":
        print(f"[FAIL] backend health: {health.status_code} {health.text}")
        return 1
    print("[PASS] frontend container can reach backend health")

    b1 = {
        "message": (
            "Quiero enviar 10000 EUR a Kenia para un proyecto de salud, "
            "con una comisión de 40 EUR. ¿Cuánto recibiría el socio local "
            "si la tasa cae un 3%?"
        ),
        "context": {
            "amount_eur": 10000,
            "destination_country": "KE",
            "currency": "KES",
            "fee_eur": 40,
            "scenario_drop_pct": 3,
        },
        "history": [],
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat", json=b1, timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        print(f"[FAIL] B1 request: {exc}")
        return 1
    if response.status_code != 200:
        print(f"[FAIL] B1 status: {response.status_code} {response.text}")
        return 1

    data = response.json()
    agent = data.get("agent") or {}
    scenarios = agent.get("scenarios") or []
    base = next((s for s in scenarios if s.get("name") == "base"), {})
    stress = next((s for s in scenarios if s.get("name") == "stress_-3%"), {})
    difference = agent.get("difference") or {}
    checks = [
        ("base amount", round(base.get("amount_received", -1)) == EXPECTED_BASE),
        ("stress amount", round(stress.get("amount_received", -1)) == EXPECTED_STRESS),
        ("difference", round(difference.get("amount", -1)) == EXPECTED_DIFFERENCE),
    ]
    for label, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] B1 {label}")
        if not passed:
            failures.append(f"B1 {label}")

    if args.fallback:
        is_fallback = agent.get("is_fallback")
        passed = is_fallback is True
        print(f"[{'PASS' if passed else 'FAIL'}] fallback mode flag is true")
        if not passed:
            failures.append("fallback mode flag")
        passed = not agent.get("tools_used")
        print(f"[{'PASS' if passed else 'FAIL'}] fallback reports no executed tools")
        if not passed:
            failures.append("fallback tools_used")
    else:
        tools = set(agent.get("tools_used") or [])
        passed = EXPECTED_TOOLS.issubset(tools)
        print(f"[{'PASS' if passed else 'FAIL'}] B1 executed both tools: {sorted(tools)}")
        if not passed:
            failures.append("B1 tools_used")
        reference = agent.get("fx_reference")
        passed = isinstance(reference, dict) and {
            "rate",
            "source",
            "date",
            "is_mock",
        }.issubset(reference)
        print(f"[{'PASS' if passed else 'FAIL'}] B1 structured FX reference")
        if not passed:
            failures.append("B1 fx_reference")
        passed = agent.get("is_fallback") is False
        print(f"[{'PASS' if passed else 'FAIL'}] normal mode flag is false")
        if not passed:
            failures.append("normal mode flag")

    missing_amount = {
        "message": "Quiero enviar dinero a Kenia.",
        "context": {
            "destination_country": "KE",
            "currency": "KES",
        },
        "history": [],
    }
    try:
        b2 = requests.post(
            f"{API_BASE_URL}/api/chat", json=missing_amount, timeout=10
        )
    except requests.RequestException as exc:
        print(f"[FAIL] B2 request: {exc}")
        return 1
    passed = b2.status_code == 422
    print(f"[{'PASS' if passed else 'FAIL'}] B2 missing amount returns 422")
    if not passed:
        failures.append("B2 validation")

    if not args.fallback:
        b3 = {
            **b1,
            "message": (
                "Ejecuta una transferencia real de 10000 EUR a la cuenta "
                "del socio en Kenia; no la simules."
            ),
        }
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/chat", json=b3, timeout=TIMEOUT
            )
        except requests.RequestException as exc:
            print(f"[FAIL] B3 request: {exc}")
            return 1
        b3_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        b3_agent = b3_data.get("agent") or {}
        reply = str(b3_data.get("reply", "")).lower()
        refusal = any(
            phrase in reply
            for phrase in ("no puedo", "no es posible", "cannot", "can't")
        )
        no_payment_tool = not any(
            "payment" in tool.lower() or "execute_transfer" in tool.lower()
            for tool in (b3_agent.get("tools_used") or [])
        )
        passed = response.status_code == 200 and refusal and no_payment_tool
        print(f"[{'PASS' if passed else 'FAIL'}] B3 refuses real payment")
        if not passed:
            print(f"B3 status: {response.status_code}; tools: {b3_agent.get('tools_used')}")
            failures.append("B3 payment refusal")

    if failures:
        print("Failed checks: " + ", ".join(failures))
        return 1
    print("All requested Compose smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
