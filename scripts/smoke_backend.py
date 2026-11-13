#!/usr/bin/env python3
"""
Smoke test del backend de Impact FX.

Comprueba que la API responde correctamente:
  1. GET  /api/health
  2. POST /api/chat con el caso B1 (10.000 EUR -> KES, fee 40, -3%)
  3. POST /api/chat con mensaje vacio -> debe devolver 400

Uso:
  # Arrancar el servidor en otra terminal:
  #   uvicorn backend.src.main:app --port 3001
  python scripts/smoke_backend.py

El test funciona sin API key: si el LLM no esta disponible, el backend
responde en modo fallback determinista y las cifras deben coincidir.
"""

from __future__ import annotations

import json
import os
import sys

import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3001").rstrip("/")
TIMEOUT = 60

EXPECTED_BASE = 1444200
EXPECTED_STRESS = 1400874
EXPECTED_DIFFERENCE = 43326


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def main() -> None:
    # 1. Health
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
    except requests.exceptions.RequestError as exc:
        fail(f"No se pudo conectar con {BASE_URL}: {exc}")

    if response.status_code != 200 or response.json().get("status") != "ok":
        fail(f"Health incorrecto: {response.status_code} {response.text}")
    print("[OK ] GET /api/health")

    # 2. Chat con el caso B1
    payload = {
        "message": (
            "Quiero enviar 10000 EUR a Kenia para un proyecto de salud, "
            "con una comision de 40 EUR. Cuanto recibiria el socio local "
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
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=TIMEOUT)
    except requests.exceptions.RequestError as exc:
        fail(f"Fallo la llamada a /api/chat: {exc}")

    if response.status_code != 200:
        fail(f"Chat incorrecto: {response.status_code} {response.text}")

    data = response.json()
    agent = data.get("agent") or {}
    scenarios = agent.get("scenarios") or []
    difference = agent.get("difference") or {}

    if len(scenarios) < 2:
        fail(f"Se esperaban 2 escenarios, se recibieron {len(scenarios)}")

    base = next((s for s in scenarios if s.get("name") == "base"), None)
    stress = next((s for s in scenarios if str(s.get("name", "")).startswith("stress")), None)

    if not base or not stress:
        fail(f"Escenarios con nombres inesperados: {[s.get('name') for s in scenarios]}")

    if round(base["amount_received"]) != EXPECTED_BASE:
        fail(f"Escenario base incorrecto: {base['amount_received']} != {EXPECTED_BASE}")

    if round(stress["amount_received"]) != EXPECTED_STRESS:
        fail(f"Escenario de estres incorrecto: {stress['amount_received']} != {EXPECTED_STRESS}")

    if round(difference.get("amount", -1)) != EXPECTED_DIFFERENCE:
        fail(f"Diferencia incorrecta: {difference.get('amount')} != {EXPECTED_DIFFERENCE}")

    if not data.get("reply"):
        fail("La respuesta no incluye 'reply'")

    tools = agent.get("tools_used") or []
    if not tools:
        print("[AVISO] La respuesta no indica herramientas usadas (modo fallback)")

    print(f"[OK ] POST /api/chat -> {json.dumps(agent.get('tools_used'))}")
    print(f"[OK ] Cifras verificadas: {EXPECTED_BASE} / {EXPECTED_STRESS} / {EXPECTED_DIFFERENCE}")

    # 3. Validacion de entrada
    bad_payload = dict(payload)
    bad_payload["message"] = ""
    response = requests.post(f"{BASE_URL}/api/chat", json=bad_payload, timeout=TIMEOUT)
    if response.status_code != 400:
        fail(f"Se esperaba 400 con mensaje vacio, se recibio {response.status_code}")
    print("[OK ] POST /api/chat con message vacio -> 400")

    print("\nSmoke test correcto.")


if __name__ == "__main__":
    main()
