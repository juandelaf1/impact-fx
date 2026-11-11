# Backend — Impact FX (FastAPI)

API REST y orquestación del agente (LLM + tools).

## Responsabilidades
- Exponer `GET /api/health` y `POST /api/chat`.
- Validar/sanitizar inputs y gestionar errores (400/422/502).
- Orquestar el LLM con *function calling* (system prompt + tools).
- Ejecutar tools contra `data/processed` e integrar resultados en la respuesta.
- Cargar configuración desde `.env` (nunca commitear claves).

## Estructura
```text
backend/
├─ requirements.txt
└─ src/
   ├─ main.py                 # app FastAPI (CORS, routers)
   ├─ api/routes.py           # /api/health, /api/chat
   ├─ agent/
   │  ├─ orchestrator.py      # bucle tool-calling + fallback determinista
   │  ├─ system_prompt.txt
   │  └─ tool_definitions.json
   ├─ tools/                  # get_fx_reference.py, calculate_transfer_scenarios.py
   ├─ services/data_loader.py  # carga de fixtures (data/processed)
   └─ config/settings.py      # .env y configuración
```

## Configuración
- Copiar `.env.example` (raíz) a `.env` y completar `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL=openai/gpt-oss-20b`, `API_BASE_URL`, etc.
- Fuente de datos: `data/processed/` (raíz del repo).

## Instalación y ejecución
Desde la raíz del repo (recomendado, para que los imports `backend.*` y rutas a datos funcionen):
```bash
pip install -r backend/requirements.txt
uvicorn backend.src.main:app --reload --port 3001
```
- Health: `GET http://localhost:3001/api/health`
- Chat: `POST http://localhost:3001/api/chat`

## Smoke test (verificación rápida)
Con el servidor arrancado en otra terminal:
```bash
python scripts/smoke_backend.py
```
Comprueba `/api/health`, el caso B1 (cifras 1.444.200 / 1.400.874 / Δ 43.326 KES) y que un `message` vacío devuelve 400. Funciona **sin API key** (el backend cae en modo fallback determinista). También se ejecuta en CI (`.github/workflows/ci.yml`).

## Contratos
- API: [`../docs/api-contract.md`](../docs/api-contract.md)
- Tools y parámetros: [`../docs/agent-design.md`](../docs/agent-design.md), [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md)
- `calculate_transfer_scenarios` requiere `currency` (ISO 4217) en el input.

## Notas
- Plan B: si falla el LLM, el orquestador devuelve un resultado determinista desde `data/processed/demo_scenarios.json` cuando hay coincidencia.
- No exponer claves; validar inputs. No commitear `.env`.
