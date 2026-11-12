from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.src.api.routes import router as api_router
from backend.src.config.settings import settings

app = FastAPI(title="Impact FX API", version="0.1.0")

origins = [o.strip() for o in settings.cors_origin.split(",") if o.strip()]
if not origins:
    origins = ["http://localhost:8501", "http://127.0.0.1:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    # Mantener contrato plano {error, code, details} cuando la API lo emite así
    if isinstance(detail, dict) and {"error", "code", "details"}.issubset(detail.keys()):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    details = "; ".join(
        f"{'.'.join(str(loc) for loc in e.get('loc', []) if loc != 'body')}: {e.get('msg', 'invalid')}"
        for e in errors
    ) or "Solicitud inválida"
    # Para /api/chat, tratamos errores de validación estructural como 422 missing_data/invalid request
    # (B2: dato faltante -> mensaje claro sin inventar cifras)
    if request.url.path.endswith("/api/chat"):
        return JSONResponse(
            status_code=422,
            content={
                "error": "missing_data",
                "code": "UNPROCESSABLE",
                "details": details or "Faltan datos requeridos para la simulación.",
            },
        )
    return JSONResponse(status_code=422, content={"detail": errors})


app.include_router(api_router)


@app.get("/")
def root():
    return {"name": "Impact FX API", "health": "/api/health", "chat": "/api/chat"}
