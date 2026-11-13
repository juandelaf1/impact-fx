#!/usr/bin/env python3
"""
Comprobacion del entorno de Impact FX (para el backend de Juan).

Verifica, sin mostrar la clave:
  1. Que existe .env en la raiz del repo.
  2. Que LLM_API_KEY y LLM_MODEL estan configurados.
  3. Que el modelo responde (una llamada minima al proveedor).
  4. Que el backend arranca y responde en /api/health y /api/chat (caso B1).

Uso:
    python scripts/check_env.py

Para el punto 3 y 4 hace falta la clave real en .env.
Si el LLM falla, el backend cae en modo fallback determinista:
el smoke test seguira verde, pero la respuesta indicara "modo fallback".
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

OK = "[OK ]"
FAIL = "[FAIL]"
WARN = "[AVISO]"


def step(title: str) -> None:
    print(f"\n--- {title} ---")


def main() -> int:
    problems = 0

    step("1) Archivo .env")
    if ENV_PATH.exists():
        print(f"{OK} .env encontrado en {ENV_PATH}")
    else:
        print(f"{FAIL} No existe .env. Copia .env.example -> .env y rellena la clave.")
        problems += 1

    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    provider = os.getenv("LLM_PROVIDER", "groq")

    step("2) Variables de configuracion")
    if api_key:
        print(f"{OK} LLM_API_KEY configurada ({len(api_key)} caracteres, no se muestra)")
    else:
        print(f"{FAIL} Falta LLM_API_KEY en .env")
        problems += 1

    if model:
        print(f"{OK} LLM_MODEL = {model}")
    else:
        print(f"{FAIL} Falta LLM_MODEL en .env (usa openai/gpt-oss-20b en Groq)")
        problems += 1

    print(f"{OK} LLM_PROVIDER = {provider}")

    if problems:
        print(f"\nCorrige {problems} problema(s) antes de continuar.")
        return 1

    step("3) Conexion con el modelo")
    try:
        # Se usa el mismo cliente que el backend para validar la configuracion real.
        sys.path.insert(0, str(PROJECT_ROOT))
        from backend.src.agent.orchestrator import _get_llm_client

        client = _get_llm_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Responde solo: OK"}],
            max_tokens=32,
        )
        content = response.choices[0].message.content
        print(f"{OK} El modelo responde ({content!r})")
    except Exception as exc:
        print(f"{FAIL} No se pudo contactar con el modelo: {exc}")
        problems += 1

    step("4) Backend local (/api/health + /api/chat)")
    port = os.getenv("PORT", "3001")
    base_url = f"http://localhost:{port}"
    process = None

    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"{OK} El backend ya estaba corriendo en {base_url}")
    except requests.exceptions.RequestException:
        print("... arrancando el backend (uvicorn) ...", flush=True)
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.src.main:app",
                "--port",
                port,
            ],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            time.sleep(1)
            try:
                response = requests.get(f"{base_url}/api/health", timeout=3)
                break
            except requests.exceptions.RequestException:
                continue
        else:
            print(f"{FAIL} El backend no arranco en {base_url}")
            problems += 1
            process.terminate()
            return 1

    try:
        payload = {
            "message": (
                "Quiero enviar 10000 EUR a Kenia con una comision de 40 EUR. "
                "Cuanto recibiria el socio local si la tasa cae un 3%?"
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
        response = requests.post(f"{base_url}/api/chat", json=payload, timeout=90)
        data = response.json()
        agent = data.get("agent") or {}

        print(f"{OK} /api/chat respondio {response.status_code}")
        print(f"     tools_used: {agent.get('tools_used')}")
        print(f"     escenarios: {[s.get('amount_received') for s in agent.get('scenarios', [])]}")
        print(f"     diferencia: {(agent.get('difference') or {}).get('amount')}")

        if "fallback" in (agent.get("reasoning_summary") or "").lower():
            print(f"{WARN} La respuesta vino del modo fallback: el LLM no participo.")
            print("     Revisa LLM_API_KEY / LLM_MODEL y el bucle de tool calling.")
        else:
            print(f"{OK} El agente real decidio y uso herramientas.")
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except Exception:
                process.kill()

    print()
    if problems:
        print(f"Listo con {problems} problema(s) pendiente(s).")
        return 1

    print("Entorno verificado: todo correcto para la sesion del reto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
