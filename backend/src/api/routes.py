from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.src.agent.orchestrator import run_agent
from backend.src.services.data_loader import default_fee_for_currency

router = APIRouter(prefix="/api")


class BudgetItem(BaseModel):
    name: str
    amount_local: float
    priority: Optional[str] = None


class ChatContext(BaseModel):
    amount_eur: float = Field(..., gt=0)
    destination_country: str
    currency: str
    fee_eur: Optional[float] = Field(default=None, ge=0)
    scenario_drop_pct: float = 3
    project_budget: Optional[list[BudgetItem]] = None


class ChatRequest(BaseModel):
    message: str
    context: ChatContext
    history: Optional[list[dict[str, Any]]] = None


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat")
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_input", "code": "BAD_REQUEST", "details": "message es requerido"},
        )

    ctx = req.context.model_dump()
    # Normalizar
    ctx["currency"] = str(ctx.get("currency", "")).upper()
    ctx["destination_country"] = str(ctx.get("destination_country", "")).upper()

    # Aplicar fee por defecto si falta (según fee_rules.json)
    if ctx.get("fee_eur") is None:
        default_fee = default_fee_for_currency(ctx["currency"])
        if default_fee is not None:
            ctx["fee_eur"] = default_fee

    # Datos mínimos para simular
    missing: list[str] = []
    if not ctx.get("currency"):
        missing.append("currency")
    if ctx.get("amount_eur") is None:
        missing.append("amount_eur")
    if ctx.get("fee_eur") is None:
        missing.append("fee_eur")

    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "missing_data",
                "code": "UNPROCESSABLE",
                "details": f"Faltan datos requeridos para la simulación: {', '.join(missing)}",
            },
        )

    try:
        result = run_agent(req.message, ctx, req.history or [])
        # Asegurar contrato mínimo
        if "reply" not in result:
            result["reply"] = ""
        if "agent" not in result:
            result["agent"] = {
                "tools_used": [],
                "scenarios": [],
                "difference": {},
                "assumptions": [],
                "alerts": [],
                "reasoning_summary": "",
            }
        return result
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "upstream_failure", "code": "LLM_OR_TOOL_ERROR", "details": str(e)},
        )
