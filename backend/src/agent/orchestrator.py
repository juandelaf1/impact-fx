from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from backend.src.config.settings import settings
from backend.src.services.data_loader import find_demo_scenario
from backend.src.tools.get_fx_reference import get_fx_reference
from backend.src.tools.calculate_transfer_scenarios import calculate_transfer_scenarios

AGENT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = AGENT_DIR / "system_prompt.txt"
TOOL_DEFS_PATH = AGENT_DIR / "tool_definitions.json"

# Solo se permite ejecutar estas funciones.
# Nunca ejecutamos codigo arbitrario generado por el modelo.
TOOL_FUNCTIONS = {
    "get_fx_reference": get_fx_reference,
    "calculate_transfer_scenarios": calculate_transfer_scenarios,
}

MAX_ROUNDS = 6


def load_system_prompt() -> str:
    with SYSTEM_PROMPT_PATH.open(encoding="utf-8") as f:
        return f.read().strip()


def load_tool_schemas() -> list[dict[str, Any]]:
    with TOOL_DEFS_PATH.open(encoding="utf-8") as f:
        definitions = json.load(f)
    # Adaptamos al formato tools de chat completions.
    return [{"type": "function", "function": definition} for definition in definitions]


def _get_llm_client():
    """
    Devuelve un cliente compatible con la API de chat completions.

    Para Groq usamos el SDK nativo (probado en los scripts del equipo).
    Para el resto usamos el cliente de OpenAI, que tambien sirve con
    proveedores compatibles (base URL configurable).
    """
    api_key = settings.llm_api_key
    if not api_key:
        raise RuntimeError("LLM_API_KEY no configurada en .env")

    provider = (settings.llm_provider or "groq").lower()

    if provider == "groq":
        try:
            from groq import Groq  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Falta la dependencia groq: {exc}")
        return Groq(api_key=api_key)

    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Falta la dependencia openai: {exc}")

    if settings.llm_base_url:
        return OpenAI(api_key=api_key, base_url=settings.llm_base_url)
    if provider == "openai":
        return OpenAI(api_key=api_key)
    return OpenAI(api_key=api_key)


def _call_llm(client: Any, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):
    """
    Llama al LLM con las tools disponibles.

    Algunos modelos (p.ej. los de razonamiento) no aceptan temperature
    o max_tokens: si la llamada falla por eso, reintentamos sin ellos.
    """
    kwargs: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }

    try:
        return client.chat.completions.create(**kwargs)
    except Exception:
        pass

    kwargs.pop("tool_choice", None)
    try:
        return client.chat.completions.create(**kwargs)
    except Exception:
        pass

    minimal = {
        "model": settings.llm_model,
        "messages": messages,
        "tools": tools,
    }
    return client.chat.completions.create(**minimal)


def _run_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    function = TOOL_FUNCTIONS.get(name)
    if not function:
        raise ValueError(f"Tool no permitida: {name}")
    return function(**arguments)


def _fallback_response(context: dict[str, Any]) -> dict[str, Any]:
    """
    Plan B: si el LLM no esta disponible devolvemos el escenario
    determinista de data/processed/demo_scenarios.json (si existe).
    """
    amount = context.get("amount_eur")
    currency = str(context.get("currency", "KES")).upper()
    variation = float(context.get("scenario_drop_pct", 3)) * -1.0
    fee = context.get("fee_eur")

    scenario = None
    try:
        if amount is not None:
            scenario = find_demo_scenario(
                float(amount),
                currency,
                variation,
                None if fee is None else float(fee),
            )
    except Exception:
        scenario = None

    if scenario:
        expected = scenario.get("expected", {})
        scenarios = expected.get("scenarios", [])
        difference = expected.get("difference", {})
        assumptions = list(
            expected.get(
                "assumptions",
                ["Modo determinista (fallback): datos de demo_scenarios.json"],
            )
        )
        tools_used = expected.get(
            "tools_used",
            ["get_fx_reference", "calculate_transfer_scenarios"],
        )
        base_amount = scenarios[0]["amount_received"] if scenarios else None
        stress_amount = scenarios[1]["amount_received"] if len(scenarios) > 1 else None
        reply = (
            f"Simulacion (modo fallback determinista) para {amount} EUR a {currency}: "
            f"escenario base {base_amount} {currency}, escenario con variacion "
            f"{stress_amount} {currency}, diferencia {difference.get('amount')} "
            f"{difference.get('currency', currency)}. "
            f"Supuestos: {'; '.join(assumptions)}."
        )
        return {
            "reply": reply,
            "agent": {
                "tools_used": tools_used,
                "reasoning_summary": (
                    "Fallback determinista usando demo_scenarios.json por "
                    "indisponibilidad del LLM."
                ),
                "scenarios": scenarios,
                "difference": difference,
                "assumptions": assumptions
                + ["Resultado generado en modo fallback (LLM no disponible)."],
                "alerts": [],
            },
        }

    return {
        "reply": (
            "No puedo completar la simulacion ahora mismo. Indica el monto (EUR), "
            "el destino/moneda, la comision y la variacion (p. ej. 3%) para "
            "intentarlo de nuevo."
        ),
        "agent": {
            "tools_used": [],
            "reasoning_summary": "Fallback sin escenario determinista coincidente.",
            "scenarios": [],
            "difference": {},
            "assumptions": [
                "No se pudo contactar el LLM y no hay un escenario determinista "
                "coincidente."
            ],
            "alerts": [],
        },
    }


def run_agent(
    message: str,
    context: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    history = history or []

    try:
        client = _get_llm_client()
        tools = load_tool_schemas()
        system_prompt = load_system_prompt()

        user_content = message
        if context:
            user_content += (
                "\n\nContexto (JSON):\n" + json.dumps(context, ensure_ascii=False)
            )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        for item in history:
            if item.get("role") in ("user", "assistant") and item.get("content"):
                messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": user_content})

        tools_used: list[str] = []
        scenarios: list[dict[str, Any]] = []
        difference: dict[str, Any] = {}
        assumptions: list[str] = []

        for _ in range(MAX_ROUNDS):
            response = _call_llm(client, messages, tools)
            choice = response.choices[0].message
            tool_calls = getattr(choice, "tool_calls", None) or []

            if not tool_calls:
                reply = choice.content or ""
                meta = {
                    "tools_used": tools_used,
                    "reasoning_summary": (
                        "El agente respondio integrando los resultados de las "
                        "herramientas."
                    ),
                    "scenarios": scenarios,
                    "difference": difference,
                    "assumptions": assumptions,
                    "alerts": [],
                }
                if not meta["assumptions"]:
                    meta["assumptions"] = [
                        "Verificar los supuestos citados en el texto de la respuesta."
                    ]
                return {"reply": reply, "agent": meta}

            messages.append(
                {
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )

            for call in tool_calls:
                name = call.function.name
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                except Exception:
                    arguments = {}

                # Si falta la moneda, la tomamos del contexto.
                if (
                    name == "calculate_transfer_scenarios"
                    and "currency" not in arguments
                    and context.get("currency")
                ):
                    arguments["currency"] = str(context["currency"]).upper()

                try:
                    result = _run_tool(name, arguments)
                except Exception as exc:
                    result = {"error": str(exc)}

                if name not in tools_used:
                    tools_used.append(name)

                if name == "calculate_transfer_scenarios" and isinstance(result, dict):
                    if "scenarios" in result:
                        scenarios = result.get("scenarios") or []
                        difference = result.get("difference") or {}
                    if result.get("error"):
                        assumptions.append(
                            f"La herramienta {name} devolvio un error: {result['error']}"
                        )

                if name == "get_fx_reference" and isinstance(result, dict):
                    if result.get("rate") is not None:
                        assumptions.append(
                            f"Tasa de referencia {result.get('rate')} "
                            f"({result.get('source')}, {result.get('date')}, "
                            f"is_mock={result.get('is_mock')})"
                        )
                    elif result.get("error"):
                        assumptions.append(
                            f"La herramienta {name} devolvio un error: {result['error']}"
                        )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Si se agotan las rondas, caemos al modo determinista.
        return _fallback_response(context)

    except Exception:
        return _fallback_response(context)
