# Backend — Impact FX (FastAPI)

API REST y orquestación del agente (LLM + tools).

## Responsabilidades
- Exponer `GET /api/health` y `POST /api/chat`.
- Validar/sanitizar inputs y gestionar errores (400/422/502) con formato de contrato.
- Orquestar el LLM con *function calling* (system prompt + tools) y ejecutar tools permitidas.
- Aplicar reglas de datos (p. ej. comisión por defecto desde `data/processed/fee_rules.json`) e integrar resultados en la respuesta.
- Cargar configuración desde `.env` (nunca commitear claves).

## Estructura
```text
backend/
├─ requirements.txt
└─ src/
   ├─ main.py                 # app FastAPI (CORS, handler de validación, routers)
   ├─ api/routes.py           # /api/health, /api/chat
   ├─ agent/
   │  ├─ orchestrator.py      # bucle tool-calling + fallback determinista
   │  ├─ system_prompt.txt
   │  └─ tool_definitions.json
   ├─ tools/                  # get_fx_reference.py, calculate_transfer_scenarios.py
   ├─ services/data_loader.py  # carga de fixtures y reglas (data/processed)
   └─ config/settings.py      # .env y configuración
```

## Configuración
- Copiar `.env.example` (raíz) a `.env` y completar `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` (opcional), `PORT`, `CORS_ORIGIN`, etc.
- Fuente de datos: `data/processed/` (raíz del repo).

## Instalación y ejecución
Desde la raíz del repo (recomendado, para que los imports `backend.*` y rutas a datos funcionen):
```bash
pip install -r backend/requirements.txt
uvicorn backend.src.main:app --reload --port 3001
```
- Health: `GET http://localhost:3001/api/health`
- Chat: `POST http://localhost:3001/api/chat`

## Comportamiento de `/api/chat`
- **400 `BAD_REQUEST` (`invalid_input`)**: `message` vacío o entrada inválida según validación de endpoint.
- **422 `UNPROCESSABLE` (`missing_data`)**: faltan datos mínimos de simulación sin valor/regla (p. ej. `currency`, `amount_eur`, `fee_eur` sin regla en `fee_rules.json`) o la validación de request de chat no es procesable (formato alineado al contrato).
- **200 con fallback determinista**: si el LLM no está disponible/falla o se agotan rondas de tool-calling, el orquestador intenta responder desde `data/processed/demo_scenarios.json` cuando hay coincidencia, añadiendo motivo/alertas de trazabilidad.
- **502 `LLM_OR_TOOL_ERROR` (`upstream_failure`)**: fallo no controlado en el endpoint/orquestación.

## Tests y verificación
```bash
# Tests unitarios
python -m unittest discover -s tests -v

# Smoke test (con servidor en otra terminal)
python scripts/smoke_backend.py

# Validación de datos
node scripts/validate-data.mjs

# Chequeo de entorno/LLM (opcional)
python scripts/check_env.py
```

El smoke test comprueba `/api/health`, el caso B1 (1.444.200 / 1.400.874 / Δ 43.326 KES) y que un `message` vacío devuelve 400. Funciona **sin API key** cuando el fallback determinista puede resolver el caso. También se ejecuta en CI (`.github/workflows/ci.yml`).

## Contratos
- API: [`../docs/api-contract.md`](../docs/api-contract.md)
- Tools y parámetros: [`../docs/agent-design.md`](../docs/agent-design.md), [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md)
- `calculate_transfer_scenarios` requiere `currency` (ISO 4217) en el input.

## Notas
- Plan B: fallback determinista desde `demo_scenarios.json` ante indisponibilidad/fallo del LLM (cuando aplica).
- No exponer claves; validar inputs. No commitear `.env`.
