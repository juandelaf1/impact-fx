from __future__ import annotations

from typing import Any, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.src.agent.orchestrator import run_agent
from backend.src.services.data_loader import default_fee_for_currency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# MVP: corredor principal soportado para simulación verificada
MVP_DESTINATION_COUNTRY = "KE"
MVP_CURRENCY = "KES"
MAX_AMOUNT_EUR = 10_000_000
MAX_FEE_EUR = 1_000_000
MAX_DROP_PCT = 100
MAX_MESSAGE_LEN = 2000
MAX_BUDGET_ITEMS = 50


class BudgetItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    amount_local: float = Field(..., gt=0, le=10_000_000_000)
    priority: Optional[str] = Field(default=None, max_length=40)


class ChatContext(BaseModel):
    amount_eur: float = Field(..., gt=0, le=MAX_AMOUNT_EUR)
    destination_country: str = Field(..., min_length=2, max_length=2)
    currency: str = Field(..., min_length=3, max_length=3)
    fee_eur: Optional[float] = Field(default=None, ge=0, le=MAX_FEE_EUR)
    scenario_drop_pct: float = Field(default=3, ge=0, lt=MAX_DROP_PCT)
    project_budget: Optional[list[BudgetItem]] = None

    @field_validator("destination_country", "currency", mode="before")
    @classmethod
    def _strip_upper(cls, v: Any) -> str:
        return str(v or "").strip().upper()


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=MAX_MESSAGE_LEN)
    context: ChatContext
    history: Optional[list[dict[str, Any]]] = None


@router.get("/health")
def health():
    return {"status": "ok"}


def _http_error(status: int, error: str, code: str, details: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": error, "code": code, "details": details})


@router.post("/chat")
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise _http_error(400, "invalid_input", "BAD_REQUEST", "message es requerido")

    ctx = req.context.model_dump()
    ctx["currency"] = str(ctx.get("currency", "")).upper().strip()
    ctx["destination_country"] = str(ctx.get("destination_country", "")).upper().strip()

    # Validación de corredor MVP: KE debe corresponder a KES (EUR→KES)
    dest = ctx.get("destination_country")
    curr = ctx.get("currency")
    if dest != MVP_DESTINATION_COUNTRY or curr != MVP_CURRENCY:
        raise _http_error(
            400,
            "invalid_input",
            "BAD_REQUEST",
            "Corredor no soportado en el MVP. Usa destino KE y moneda KES (EUR→KES).",
        )

    # Límites razonables adicionales
    if ctx.get("fee_eur") is not None and float(ctx["fee_eur"]) > float(ctx["amount_eur"]):
        raise _http_error(400, "invalid_input", "BAD_REQUEST", "La comisión no puede ser mayor que el importe enviado.")
    project_budget = ctx.get("project_budget") or []
    if len(project_budget) > MAX_BUDGET_ITEMS:
        raise _http_error(400, "invalid_input", "BAD_REQUEST", "project_budget excede el límite permitido.")

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
        result = run_agent(req.message, ctx, req.history or [])
        if "reply" not in result:
            result["reply"] = ""
        if "agent" not in result or not isinstance(result.get("agent"), dict):
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
                "fx_reference": None,
                "is_fallback": True,
            }
        return result
    except Exception:
        logger.exception("Error interno en /api/chat")
        raise _http_error(
            502,
            "upstream_failure",
            "LLM_OR_TOOL_ERROR",
            "No se pudo completar la solicitud en este momento. Inténtalo de nuevo más tarde.",
        )
