from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.routes import router as api_router
from backend.src.config.settings import settings

app = FastAPI(title="Impact FX API", version="0.1.0")

origins = [o.strip() for o in settings.cors_origin.split(",") if o.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"name": "Impact FX API", "health": "/api/health", "chat": "/api/chat"}
