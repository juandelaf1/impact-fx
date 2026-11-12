from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from backend.src.config.settings import settings
from backend.src.services.data_loader import find_demo_scenario, load_json
from backend.src.services.budget_impact import calculate_budget_impact
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


def _maybe_budget_impact(context: dict[str, Any], scenarios: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not scenarios or len(scenarios) < 2:
        return None
    dest = str(context.get("destination_country", "")).upper()
    currency = str(context.get("currency", "")).upper()
    if dest != "KE" or currency != "KES":
        return None
    try:
        budgets = load_json("project_budgets.json")
        project = next((b for b in budgets if str(b.get("project_id")) == "KE-HEALTH-001"), None)
        if not project:
            return None
        base = scenarios[0].get("amount_received")
        stress = scenarios[1].get("amount_received")
        if base is None or stress is None:
            return None
        return calculate_budget_impact(float(base), float(stress), project)
    except Exception:
        return None


def _fallback_response(context: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    """
    Plan B: si el LLM no esta disponible devolvemos el escenario
    determinista de data/processed/demo_scenarios.json (si existe).

    No atribuye tools no ejecutadas y marca la respuesta como degradada.
    """
    fallback_note = reason or "LLM no disponible o no se pudo completar la orquestación."
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
        base_amount = scenarios[0]["amount_received"] if scenarios else None
        stress_amount = scenarios[1]["amount_received"] if len(scenarios) > 1 else None
        budget_impact = _maybe_budget_impact(context, scenarios)
        reply = (
            f"Simulación (modo fallback determinista, sin ejecución LLM/tools) para {amount} EUR a {currency}: "
            f"escenario base {base_amount} {currency}, escenario con variación "
            f"{stress_amount} {currency}, diferencia potencial {difference.get('amount')} "
            f"{difference.get('currency', currency)}. "
            "Resultados basados en fixture demo_scenarios.json; estimación, no cotización firme."
        )
        if budget_impact:
            reply += (
                f" Impacto presupuestario (proyecto demo {budget_impact.get('project_id')}): "
                f"cobertura base {budget_impact.get('base_coverage_pct')}%, "
                f"cobertura bajo estrés {budget_impact.get('stress_coverage_pct')}%, "
                f"brecha potencial {budget_impact.get('budget_gap')} {budget_impact.get('currency')}."
            )
        agent = {
            "tools_used": [],
            "reasoning_summary": (
                "Fallback determinista usando demo_scenarios.json (sin flujo LLM/tools ejecutado). "
                + fallback_note
            ),
            "scenarios": scenarios,
            "difference": difference,
            "assumptions": assumptions
            + [f"Resultado generado en modo fallback degradado: {fallback_note}"],
            "alerts": [
                "Respuesta generada en modo fallback determinista (sin ejecución de tools del agente)."
            ],
            "execution_mode": "deterministic_fallback",
            "degraded": True,
            "fx_source": "demo",
            "calculation_source": "demo_scenarios",
            "fx_reference": None,
            "is_fallback": True,
        }
        if budget_impact:
            agent["budget_impact"] = budget_impact
            agent["assumptions"].append("Impacto presupuestario calculado con presupuesto sintético/de demostración (KE-HEALTH-001).")
        return {"reply": reply, "agent": agent}

    return {
        "reply": (
            "No puedo completar la simulación ahora mismo. Indica el monto (EUR), "
            "el destino/moneda, la comisión y la variación (p. ej. 3%) para "
            "intentarlo de nuevo."
        ),
        "agent": {
            "tools_used": [],
            "reasoning_summary": "Fallback sin escenario determinista coincidente. " + fallback_note,
            "scenarios": [],
            "difference": {},
            "assumptions": [
                "No hay un escenario determinista coincidente para los datos proporcionados.",
                f"Motivo: {fallback_note}",
            ],
            "alerts": ["No se pudo completar la simulación con los datos disponibles."],
            "execution_mode": "deterministic_fallback",
            "degraded": True,
            "fx_source": "demo",
            "calculation_source": "demo_scenarios",
            "fx_reference": None,
            "is_fallback": True,
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
            user_content += "\n\nContexto (JSON):\n" + json.dumps(context, ensure_ascii=False)

        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for item in history:
            if item.get("role") in ("user", "assistant") and item.get("content"):
                messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": user_content})

        tools_used: list[str] = []
        scenarios: list[dict[str, Any]] = []
        difference: dict[str, Any] = {}
        assumptions: list[str] = []
        fx_reference: dict[str, Any] | None = None
        calc_result: dict[str, Any] | None = None

        # Par?metros financieros confiables desde contexto validado/reglas (no desde el LLM)
        trusted_currency = str(context.get("currency", "")).upper().strip()
        trusted_amount = context.get("amount_eur")
        trusted_fee = context.get("fee_eur")
        try:
            trusted_drop_pct = float(context.get("scenario_drop_pct", 3) or 3)
        except Exception:
            trusted_drop_pct = 3.0
        trusted_variation = -abs(trusted_drop_pct)
        trusted_base = "EUR"
        trusted_quote = trusted_currency

        for _ in range(MAX_ROUNDS):
            response = _call_llm(client, messages, tools)
            choice = response.choices[0].message
            tool_calls = getattr(choice, "tool_calls", None) or []

            if not tool_calls:
                reply = choice.content or ""
                verified = (
                    fx_reference is not None
                    and calc_result is not None
                    and isinstance(calc_result.get("scenarios"), list)
                    and len(calc_result.get("scenarios", [])) >= 2
                    and isinstance(calc_result.get("difference"), dict)
                )
                if verified:
                    scenarios = calc_result.get("scenarios") or []
                    difference = calc_result.get("difference") or {}
                    fx_source = "frankfurter" if str(fx_reference.get("source")) == "frankfurter" else "demo"
                    budget_impact = _maybe_budget_impact(context, scenarios)
                    fx_meta = None
                    if isinstance(fx_reference, dict):
                        fx_meta = {
                            "rate": fx_reference.get("rate"),
                            "source": fx_reference.get("source"),
                            "date": fx_reference.get("date"),
                            "is_mock": fx_reference.get("is_mock"),
                        }
                    meta = {
                        "tools_used": tools_used,
                        "reasoning_summary": "Simulación completada con herramientas verificadas y parámetros financieros controlados por backend.",
                        "scenarios": scenarios,
                        "difference": difference,
                        "assumptions": assumptions or ["Verificar los supuestos citados en el texto de la respuesta."],
                        "alerts": [],
                        "execution_mode": "llm_tools",
                        "degraded": False,
                        "fx_source": fx_source,
                        "calculation_source": "financial_engine",
                        "fx_reference": fx_meta,
                        "is_fallback": False,
                    }
                    if budget_impact:
                        meta["budget_impact"] = budget_impact
                        meta["assumptions"].append("Impacto presupuestario calculado con presupuesto sintético/de demostración (KE-HEALTH-001). No se asigna el déficit a partidas concretas.")
                    return {"reply": reply, "agent": meta}

                # Sin simulación determinista verificada: no exponer escenarios no respaldados
                fx_meta = None
                if isinstance(fx_reference, dict):
                    fx_meta = {
                        "rate": fx_reference.get("rate"),
                        "source": fx_reference.get("source"),
                        "date": fx_reference.get("date"),
                        "is_mock": fx_reference.get("is_mock"),
                    }
                meta = {
                    "tools_used": tools_used,
                    "reasoning_summary": "No se completó una simulación financiera verificada por herramientas.",
                    "scenarios": [],
                    "difference": {},
                    "assumptions": assumptions or ["No hay resultados deterministas verificados disponibles."],
                    "alerts": ["No hay escenarios respaldados por cálculo determinista verificado en esta respuesta."],
                    "execution_mode": "llm_tools",
                    "degraded": True,
                    "fx_source": ("frankfurter" if fx_reference and str(fx_reference.get("source")) == "frankfurter" else "demo"),
                    "calculation_source": "none",
                    "fx_reference": fx_meta,
                    "is_fallback": False,
                }
                # Si el contexto permite simulación determinista, preferir fallback honesto
                if trusted_amount is not None and trusted_currency and trusted_fee is not None:
                    fb = _fallback_response(context, reason="No se obtuvo simulación verificada (FX + cálculo) en el flujo LLM.")
                    # conservar trazas útiles si existen
                    if assumptions:
                        fb_agent = fb.get("agent", {})
                        fb_agent.setdefault("assumptions", [])
                        fb["agent"] = fb_agent
                    return fb
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
                    _ = json.loads(call.function.arguments or "{}")
                except Exception:
                    _ = {}

                # Binding/validaci?n de argumentos desde fuentes confiables
                if name == "get_fx_reference":
                    if not trusted_base or not trusted_quote or len(trusted_quote) != 3:
                        result = {"error": "Corredor/moneda no disponible o inv?lido en contexto validado."}
                    else:
                        safe_args = {"base": trusted_base, "quote": trusted_quote}
                        try:
                            result = _run_tool(name, safe_args)
                        except Exception as exc:
                            result = {"error": str(exc)}
                elif name == "calculate_transfer_scenarios":
                    if fx_reference is None or fx_reference.get("rate") is None:
                        result = {"error": "No hay tasa de referencia verificada. Ejecuta get_fx_reference primero."}
                    elif trusted_amount is None or trusted_fee is None or not trusted_currency:
                        result = {"error": "Faltan par?metros financieros confiables en el contexto."}
                    else:
                        safe_args = {
                            "amount_eur": float(trusted_amount),
                            "rate": float(fx_reference["rate"]),
                            "fee_eur": float(trusted_fee),
                            "variations": [trusted_variation],
                            "currency": trusted_currency,
                        }
                        try:
                            result = _run_tool(name, safe_args)
                        except Exception as exc:
                            result = {"error": str(exc)}
                else:
                    result = {"error": f"Tool no soportada: {name}"}

                # Registrar tool_used solo si ejecuci?n exitosa (sin error)
                if isinstance(result, dict) and not result.get("error"):
                    if name not in tools_used:
                        tools_used.append(name)

                if name == "calculate_transfer_scenarios" and isinstance(result, dict):
                    if not result.get("error") and "scenarios" in result and "difference" in result:
                        calc_result = result
                        scenarios = result.get("scenarios") or []
                        difference = result.get("difference") or {}
                    elif result.get("error"):
                        calc_result = None
                        scenarios = []
                        difference = {}
                        assumptions.append(f"La herramienta {name} devolvi? un error: {result['error']}")

                if name == "get_fx_reference" and isinstance(result, dict):
                    if result.get("rate") is not None and not result.get("error"):
                        fx_reference = {
                            "rate": result.get("rate"),
                            "source": result.get("source"),
                            "date": result.get("date"),
                            "is_mock": result.get("is_mock"),
                        }
                        assumptions.append(
                            f"Tasa de referencia {fx_reference.get('rate')} ({fx_reference.get('source')}, {fx_reference.get('date')}, is_mock={fx_reference.get('is_mock')})"
                        )
                    elif result.get("error"):
                        fx_reference = None
                        assumptions.append(f"La herramienta {name} devolvió un error: {result['error']}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Si se agotan las rondas, caemos al modo determinista.
        return _fallback_response(context, reason="Se agotaron las rondas de tool-calling del LLM.")

    except Exception as exc:
        return _fallback_response(context, reason=f"Fallo del LLM u orquestaci?n: {exc}")
