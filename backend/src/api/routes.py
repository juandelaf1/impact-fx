from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from backend.src.agent.orchestrator import run_agent
from backend.src.config.settings import settings
from backend.src.core.logging import get_logger
from backend.src.core.rate_limit import RateLimiter
from backend.src.services.data_loader import (
    default_fee_for_currency,
    find_corridor,
    load_json,
    supported_corridors,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api")

# Límites de negocio del MVP (contrato congelado, ver docs/api-contract.md).
MAX_AMOUNT_EUR = 10_000_000
MAX_FEE_EUR = 1_000_000
MAX_DROP_PCT = 100
MAX_MESSAGE_LEN = 2000
MAX_BUDGET_ITEMS = 50

# Límite de tasa del endpoint de simulación (configurable por entorno).
# Protege el consumo de créditos del proveedor LLM.
rate_limiter = RateLimiter(
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


class BudgetItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    amount_local: float = Field(..., gt=0, le=10_000_000_000)
    priority: str | None = Field(default=None, max_length=40)


class ChatContext(BaseModel):
    amount_eur: float = Field(..., gt=0, le=MAX_AMOUNT_EUR)
    destination_country: str = Field(..., min_length=2, max_length=2)
    currency: str = Field(..., min_length=3, max_length=3)
    fee_eur: float | None = Field(default=None, ge=0, le=MAX_FEE_EUR)
    scenario_drop_pct: float = Field(default=3, ge=0, lt=MAX_DROP_PCT)
    project_budget: list[BudgetItem] | None = None

    @field_validator("destination_country", "currency", mode="before")
    @classmethod
    def _strip_upper(cls, v: Any) -> str:
        return str(v or "").strip().upper()


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=MAX_MESSAGE_LEN)
    context: ChatContext
    history: list[dict[str, Any]] | None = None


@router.get("/health")
def health():
    """Sonda de liveness: el proceso responde."""

    return {"status": "ok"}


@router.get("/ready")
def ready():
    """Sonda de readiness: dependencias críticas disponibles.

    No llama al LLM (coste/latencia): comprueba que los datos y las reglas
    de negocio que el backend necesita están cargables.
    """

    checks: dict[str, Any] = {}
    ready_state = True

    for name in ("fx_rates.json", "fee_rules.json", "corridors.json"):
        try:
            load_json(name)
            checks[name] = "ok"
        except Exception as exc:  # pragma: no cover - defensivo
            checks[name] = f"error: {exc}"
            ready_state = False

    checks["llm_configured"] = bool(settings.llm_api_key)
    checks["fx_source"] = settings.fx_source

    return {
        "status": "ready" if ready_state else "degraded",
        "checks": checks,
        "version": settings.app_version,
    }


@router.get("/version")
def version():
    """Versión del servicio (para despliegues y diagnóstico)."""

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


def _http_error(status: int, error: str, code: str, details: str) -> HTTPException:
    return HTTPException(
        status_code=status, detail={"error": error, "code": code, "details": details}
    )


def _client_key(request: Request) -> str:
    """Clave de agrupación para el limitador de tasa (IP o proxy conocido)."""

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/chat")
def chat(req: ChatRequest, request: Request):
    # 1) Límite de tasa: protege el consumo de créditos del proveedor LLM.
    if settings.rate_limit_enabled:
        rate_result = rate_limiter.check(_client_key(request))
        if not rate_result.allowed:
            logger.warning(
                "rate_limited",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "fields": {"client": _client_key(request), "path": request.url.path},
                },
            )
            raise _http_error(
                429,
                "rate_limited",
                "TOO_MANY_REQUESTS",
                f"Demasiadas peticiones. Inténtalo de nuevo en {rate_result.retry_after} s.",
            )

    if not req.message or not req.message.strip():
        raise _http_error(400, "invalid_input", "BAD_REQUEST", "message es requerido")

    history = req.history or []
    if len(history) > settings.max_history_messages:
        raise _http_error(
            400,
            "invalid_input",
            "BAD_REQUEST",
            f"history excede el límite permitido ({settings.max_history_messages} mensajes).",
        )

    ctx = req.context.model_dump()
    ctx["currency"] = str(ctx.get("currency", "")).upper().strip()
    ctx["destination_country"] = str(ctx.get("destination_country", "")).upper().strip()

    # Validación de corredor MVP: la matriz de cobertura vive en los datos.
    corridor = find_corridor(
        str(ctx.get("destination_country") or ""),
        str(ctx.get("currency") or ""),
    )
    if corridor is None:
        available = ", ".join(
            f"{c.get('origin')}→{c.get('currency')} ({c.get('destination_country')})"
            for c in supported_corridors()
        )
        raise _http_error(
            400,
            "invalid_input",
            "BAD_REQUEST",
            f"Corredor no soportado en el MVP. Corredores disponibles: {available or 'ninguno'}.",
        )

    # Límites razonables adicionales
    if ctx.get("fee_eur") is not None and float(ctx["fee_eur"]) > float(ctx["amount_eur"]):
        raise _http_error(
            400,
            "invalid_input",
            "BAD_REQUEST",
            "La comisión no puede ser mayor que el importe enviado.",
        )
    project_budget = ctx.get("project_budget") or []
    if len(project_budget) > MAX_BUDGET_ITEMS:
        raise _http_error(
            400, "invalid_input", "BAD_REQUEST", "project_budget excede el límite permitido."
        )

    # Aplicar fee por defecto si falta (según fee_rules.json)
    if ctx.get("fee_eur") is None:
        default_fee = default_fee_for_currency(ctx["currency"])
        if default_fee is not None:
            ctx["fee_eur"] = default_fee

    # Datos mínimos para simular (B2: 422 missing_data con detalle claro)
    missing: list[str] = []
    if ctx.get("amount_eur") is None:
        missing.append("amount_eur")
    if not ctx.get("currency"):
        missing.append("currency")
    if ctx.get("fee_eur") is None:
        missing.append("fee_eur")

    if missing:
        raise _http_error(
            422,
            "missing_data",
            "UNPROCESSABLE",
            f"Faltan datos requeridos para la simulación: {', '.join(missing)}. Indica el/los dato(s) faltante(s) para continuar.",
        )

    try:
        result = run_agent(req.message, ctx, history)
        if "reply" not in result:
            result["reply"] = ""
        agent = result.get("agent")
        if not isinstance(agent, dict):
            result["agent"] = {
                "tools_used": [],
                "scenarios": [],
                "difference": {},
                "assumptions": [],
                "alerts": [],
                "reasoning_summary": "",
                "execution_mode": "deterministic_fallback",
                "degraded": True,
                "fx_source": "demo",
                "calculation_source": "demo_scenarios",
            }
        else:
            # Honestidad: si el usuario envía un presupuesto, el MVP todavía
            # no lo aplica (usa el presupuesto demo del corredor). Se avisa.
            if project_budget:
                alerts = agent.setdefault("alerts", [])
                note = (
                    "El presupuesto enviado por el usuario no se aplica todavía en el MVP: "
                    "el impacto presupuestario mostrado usa el presupuesto sintético del corredor."
                )
                if note not in alerts:
                    alerts.append(note)
        return result
    except Exception as exc:
        logger.exception(
            "Error interno en /api/chat",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "fields": {"path": request.url.path},
            },
        )
        raise _http_error(
            502,
            "upstream_failure",
            "LLM_OR_TOOL_ERROR",
            "No se pudo completar la solicitud en este momento. Inténtalo de nuevo más tarde.",
        ) from exc
