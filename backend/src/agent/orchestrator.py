from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.src.config.settings import settings
from backend.src.services.data_loader import find_demo_scenario
from backend.src.tools.get_fx_reference import get_fx_reference
from backend.src.tools.calculate_transfer_scenarios import calculate_transfer_scenarios

AGENT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = AGENT_DIR / "system_prompt.txt"
TOOL_DEFS_PATH = AGENT_DIR / "tool_definitions.json"

TOOL_FUNCTIONS = {
    "get_fx_reference": get_fx_reference,
    "calculate_transfer_scenarios": calculate_transfer_scenarios,
}


def load_system_prompt() -> str:
    with SYSTEM_PROMPT_PATH.open(encoding="utf-8") as f:
        return f.read().strip()


def load_tool_schemas() -> list[dict[str, Any]]:
    with TOOL_DEFS_PATH.open(encoding="utf-8") as f:
        defs = json.load(f)
    # Adaptar a formato OpenAI/Groq chat.completions
    return [{"type": "function", "function": d} for d in defs]


def _get_llm_client():
    api_key = settings.llm_api_key
    if not api_key:
        raise RuntimeError("LLM_API_KEY no configurada")
    provider = (settings.llm_provider or "groq").lower()
    base_url = settings.llm_base_url
    # Groq es compatible con el cliente OpenAI
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Falta dependencia openai: {e}")

    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    if provider == "groq":
        return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    if provider == "openai":
        return OpenAI(api_key=api_key)
    # fallback genérico
    return OpenAI(api_key=api_key, base_url=base_url or None)


def _run_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        raise ValueError(f"Tool desconocida: {name}")
    return fn(**arguments)


def _fallback_response(message: str, context: dict[str, Any]) -> dict[str, Any]:
    amount = context.get("amount_eur")
    currency = str(context.get("currency", "KES")).upper()
    variation = float(context.get("scenario_drop_pct", 3)) * -1.0
    fee = context.get("fee_eur")
    scenario = None
    try:
        if amount is not None:
            scenario = find_demo_scenario(float(amount), currency, variation, None if fee is None else float(fee))
    except Exception:
        scenario = None

    if scenario:
        expected = scenario.get("expected", {})
        scenarios = expected.get("scenarios", [])
        diff = expected.get("difference", {})
        assumptions = expected.get("assumptions", [
            "Modo determinista (fallback): datos de demo_scenarios.json"
        ])
        tools_used = expected.get("tools_used", ["get_fx_reference", "calculate_transfer_scenarios"])
        base_amt = scenarios[0]["amount_received"] if scenarios else None
        stress_amt = scenarios[1]["amount_received"] if len(scenarios) > 1 else None
        reply = (
            f"Simulación (modo fallback determinista) para {amount} EUR a {currency}: "
            f"escenario base {base_amt} {currency}, escenario con variación {stress_amt} {currency}, "
            f"diferencia {diff.get('amount')} {diff.get('currency', currency)}. "
            f"Supuestos: {'; '.join(assumptions)}."
        )
        return {
            "reply": reply,
            "agent": {
                "tools_used": tools_used,
                "reasoning_summary": "Fallback determinista usando demo_scenarios.json por indisponibilidad del LLM.",
                "scenarios": scenarios,
                "difference": diff,
                "assumptions": assumptions + ["Resultado generado en modo fallback (LLM no disponible)."],
                "alerts": [],
            },
        }

    return {
        "reply": "No puedo completar la simulación ahora mismo. Indica monto (EUR), destino/moneda, comisión y variación (p. ej. 3%) para intentarlo de nuevo.",
        "agent": {
            "tools_used": [],
            "reasoning_summary": "Fallback sin escenario coincidente.",
            "scenarios": [],
            "difference": {},
            "assumptions": ["No se pudo contactar el LLM y no hay un escenario determinista coincidente."],
            "alerts": [],
        },
    }


def run_agent(message: str, context: dict[str, Any], history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    history = history or []
    try:
        client = _get_llm_client()
        tools = load_tool_schemas()
        system_prompt = load_system_prompt()

        user_content = message
        if context:
            user_content += "\n\nContexto (JSON):\n" + json.dumps(context, ensure_ascii=False)

        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        # history esperada como [{role, content}, ...]
        for h in history:
            if h.get("role") in ("user", "assistant") and h.get("content"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_content})

        tools_used: list[str] = []
        last_tool_scenarios = None
        last_tool_difference = None
        last_assumptions: list[str] = []

        for _ in range(6):
            resp = client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
            )
            choice = resp.choices[0].message
            tool_calls = getattr(choice, "tool_calls", None) or []

            if not tool_calls:
                reply = choice.content or ""
                agent_meta = {
                    "tools_used": tools_used,
                    "reasoning_summary": "El agente respondió integrando los resultados de las herramientas.",
                    "scenarios": last_tool_scenarios or [],
                    "difference": last_tool_difference or {},
                    "assumptions": last_assumptions or [],
                    "alerts": [],
                }
                # Intentar extraer supuestos básicos si faltan
                if not agent_meta["assumptions"]:
                    agent_meta["assumptions"] = ["Verificar supuestos en el texto de la respuesta."]
                return {"reply": reply, "agent": agent_meta}

            # Añadir mensaje del asistente con tool_calls
            messages.append({
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ],
            })

            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                # Normalizar: si falta currency en calculate_transfer_scenarios, tomar del contexto
                if name == "calculate_transfer_scenarios" and "currency" not in args:
                    if context.get("currency"):
                        args["currency"] = str(context.get("currency")).upper()
                try:
                    result = _run_tool(name, args)
                except Exception as e:
                    result = {"error": str(e)}

                tools_used.append(name)
                if name == "calculate_transfer_scenarios" and isinstance(result, dict) and "scenarios" in result:
                    last_tool_scenarios = result.get("scenarios")
                    last_tool_difference = result.get("difference")
                if name == "get_fx_reference" and isinstance(result, dict) and result.get("rate") is not None:
                    last_assumptions.append(
                        f"Tasa de referencia {result.get('rate')} ({result.get('source')}, {result.get('date')}, is_mock={result.get('is_mock')})"
                    )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        # Si se agotan iteraciones
        return _fallback_response(message, context)

    except Exception:
        return _fallback_response(message, context)
