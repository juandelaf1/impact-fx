# Backend — Impact FX (FastAPI)

API REST y orquestación del agente (LLM + tools).

## Responsabilidades

- Exponer `GET /api/health`, `GET /api/ready`, `GET /api/version` y `POST /api/chat`.
- Validar/sanitizar inputs y gestionar errores (400/422/429/502) con el formato de contrato `{error, code, details}`.
- Orquestar el LLM con *function calling* (system prompt + tools) y ejecutar solo las tools permitidas.
- Aplicar reglas de datos (p. ej. comisión por defecto desde `data/processed/fee_rules.json`, corredor soportado desde `corridors.json`) e integrar los resultados en la respuesta.
- Proteger el servicio: límite de tasa por cliente, `request_id` en todas las respuestas y logs estructurados JSON.
- Cargar la configuración desde `.env` (nunca commitear claves).

## Estructura

```text
backend/
├── requirements.in            # rangos declarados de dependencias
├── requirements.txt            # lockfile reproducible (pip-compile)
└── src/
    ├── main.py                 # app FastAPI (CORS, middleware, handlers de error, routers)
    ├── api/
    │   ├── routes.py           # /api/health, /api/ready, /api/version, /api/chat
    │   └── middleware.py       # request_id + logging por petición
    ├── agent/
    │   ├── orchestrator.py     # bucle tool-calling + fallback determinista
    │   ├── system_prompt.txt
    │   └── tool_definitions.json
    ├── tools/                  # get_fx_reference.py, calculate_transfer_scenarios.py
    ├── services/
    │   ├── data_loader.py      # carga de fixtures y reglas (con caché en memoria)
    │   └── budget_impact.py    # cobertura y brecha presupuestaria
    ├── core/                   # logging JSON, contexto (request_id), limitador de tasa
    └── config/settings.py      # configuración central por entorno
```

## Configuración

- Copiar `.env.example` (raíz) a `.env` y completar `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` (opcional), `PORT`, `CORS_ORIGIN`, `RATE_LIMIT_*`, `LLM_TIMEOUT_SECONDS`, `LOG_FORMAT`…
- Fuente de datos: `data/processed/` (raíz del repo).

## Instalación y ejecución

Desde la raíz del repo (recomendado, para que los imports `backend.*` y las rutas a datos funcionen):

```bash
pip install -r backend/requirements.txt
uvicorn backend.src.main:app --reload --port 3001
```

- Health: `GET http://localhost:3001/api/health`
- Readiness: `GET http://localhost:3001/api/ready`
- Documentación: `http://localhost:3001/api/docs`

## Comportamiento de `/api/chat`

- **400 `BAD_REQUEST` (`invalid_input`)**: `message` vacío, corredor no soportado, comisión mayor que el importe o `history` por encima del límite.
- **422 `UNPROCESSABLE` (`missing_data`)**: faltan datos mínimos de simulación sin valor/regla (p. ej. `currency`, `amount_eur`, `fee_eur` sin regla en `fee_rules.json`).
- **429 `TOO_MANY_REQUESTS` (`rate_limited`)**: se ha superado el límite de peticiones por cliente (`RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`).
- **200 con fallback determinista**: si el LLM no está disponible/falla o se agotan rondas de tool-calling, el orquestador responde desde `data/processed/demo_scenarios.json` cuando hay coincidencia, con motivo y alertas de trazabilidad.
- **502 `LLM_OR_TOOL_ERROR` (`upstream_failure`)**: fallo no controlado en el endpoint/orquestación (mensaje público sanitizado).

## Tests y verificación

```bash
# Suite completa (unitarios + API HTTP + servicios frontend)
pytest tests -q

# Solo el backend, con cobertura
coverage run --source=backend -m pytest tests -q && coverage report

# Lint, formato y tipado
ruff check . && ruff format --check .
mypy backend

# Smoke test (con el servidor en otra terminal)
python scripts/smoke_backend.py

# Validación de datos
node scripts/validate-data.mjs

# Chequeo de entorno/LLM (opcional)
python scripts/check_env.py
```

El smoke test comprueba `/api/health`, el caso B1 (1.444.200 / 1.400.874 / Δ 43.326 KES) y que un `message` vacío devuelve 400. Funciona **sin API key** cuando el fallback determinista puede resolver el caso. También se ejecuta en CI (`.github/workflows/ci.yml`).

## Contratos

- API: [`../docs/api-contract.md`](../docs/api-contract.md) (incluye las extensiones aditivas v0.2)
- Tools y parámetros: [`../docs/agent-design.md`](../docs/agent-design.md), [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md)
- `calculate_transfer_scenarios` requiere `currency` (ISO 4217) en el input.

## Notas

- Plan B: fallback determinista desde `demo_scenarios.json` ante indisponibilidad/fallo del LLM.
- No exponer claves; validar inputs; no commitear `.env`.
- El limitador de tasa es **por proceso**: con varias réplicas hay que migrarlo a un contador compartido (ver `docs/tech-debt.md`, TD-10).
