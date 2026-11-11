from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.src.agent.orchestrator import run_agent

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
        raise HTTPException(status_code=400, detail={"error": "invalid_input", "code": "BAD_REQUEST", "details": "message es requerido"})

    ctx = req.context.model_dump()
    # Normalizar
    ctx["currency"] = str(ctx.get("currency", "")).upper()
    ctx["destination_country"] = str(ctx.get("destination_country", "")).upper()

    # Aplicar fee por defecto si falta (regla simple EUR-KES)
    if ctx.get("fee_eur") is None:
        if ctx["currency"] == "KES":
            ctx["fee_eur"] = 40.0
        elif ctx["currency"] == "GHS":
            ctx["fee_eur"] = 35.0

    try:
        result = run_agent(req.message, ctx, req.history or [])
        # Asegurar contrato mínimo
        if "reply" not in result:
            result["reply"] = ""
        if "agent" not in result:
            result["agent"] = {"tools_used": [], "scenarios": [], "difference": {}, "assumptions": [], "alerts": [], "reasoning_summary": ""}
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": "upstream_failure", "code": "LLM_OR_TOOL_ERROR", "details": str(e)})
