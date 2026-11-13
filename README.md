<p align="center">
  <img src="docs/assets/impact-fx-banner.png" alt="Impact FX banner" width="100%" />
</p>

<h1 align="center">Impact FX</h1>
<p align="center"><strong>Simulación transparente del impacto cambiario en transferencias para proyectos sociales</strong></p>
<p align="center">Agente de IA (MVP) que estima cuánto recibe realmente un socio local, compara escenarios de tipo de cambio y comunica el impacto con trazabilidad, supuestos explícitos y límites claros.</p>

<p align="center">
  <a href="https://github.com/juandelaf1/impact-fx/actions/workflows/ci.yml"><img src="https://github.com/juandelaf1/impact-fx/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B%20%7C%203.13-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/LLM-Tool%20Calling%20(Groq%20%7C%20OpenAI--compatible)-412991?logo=openai&logoColor=white" alt="LLM Tool Calling" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker Compose" />
  <img src="https://img.shields.io/badge/Node.js-18%2B%20(data%20validation)-339933?logo=nodedotjs&logoColor=white" alt="Node.js" />
  <img src="https://img.shields.io/badge/Tests-46%20passing%20%7C%20coverage%2064%25-success" alt="Tests y cobertura" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT" /></a>
  <img src="https://img.shields.io/badge/Status-MVP%20operativo-orange" alt="Status MVP" />
  <img src="https://img.shields.io/badge/ODS-9%20%7C%2010%20%7C%2017-0a7ea4" alt="ODS 9,10,17" />
</p>

---

## 1. Visión general

**Impact FX** ayuda a ONG y equipos de proyectos sociales a **anticipar el importe neto recibido en moneda local** ante variaciones de tipo de cambio y comisiones, reduciendo incertidumbre en la planificación y la comunicación con socios locales.

| Para quién | Problema | Qué aporta Impact FX |
|---|---|---|
| ONG / gestores de proyectos | El importe recibido puede variar por FX y comisiones, afectando actividades y presupuesto | Estimación rápida y explicable del monto recibido y la diferencia bajo estrés |
| Socios locales / coordinación | Falta de visibilidad compartida sobre supuestos y riesgos cambiarios | Respuesta integrada con cifras, supuestos, fuente/fecha y límites |
| Equipos técnicos/demo | Necesidad de un MVP fiable y auditable | Flujo determinista verificable, metadatos de ejecución y modos de degradación transparentes |

### Caso demo (golden case B1)

**Entrada:** 10.000 EUR → Kenia (KES), comisión 40 EUR, tasa ref. 145 KES/EUR (demo/ficticia), variación −3 %

**Resultado esperado:**

- **Base:** 1.444.200 KES
- **Estrés (−3 %):** 1.400.874 KES
- **Diferencia:** 43.326 KES
- **Impacto presupuestario demo (KE-HEALTH-001, sintético):** cobertura base 100 %, estrés 97 %, brecha 43.326 KES

> Las cifras se validan contra `data/processed/demo_scenarios.json` y el motor determinista (tests + smoke en CI).

### Arquitectura y flujo

```text
Usuario (Streamlit UI)
   │  POST /api/chat
   ▼
FastAPI (validación, CORS, límite de tasa, request_id, contrato de errores)
   ▼
Orquestador del agente (LLM + tool-calling + guardrails)
   ├─ get_fx_reference (tasa/fuente/fecha/is_mock)
   ├─ calculate_transfer_scenarios (cálculo determinista)
   └─ verificación + metadatos + (budget_impact demo)
   ▼
Respuesta integrada (reply + agent.* trazable)
   │
   ├─ llm_tools (verificado)
   ├─ degradado (sin verificación completa, sin inventar escenarios)
   └─ deterministic_fallback (sin LLM/tools simulados, fixtures demo)
```

**Principios de diseño:** determinismo donde importa, trazabilidad contractual, honestidad en modos degradados/fallback y separación de responsabilidades FE/BE/agente/tools. Los parámetros financieros **nunca** los decide el modelo: los fija el backend desde el contexto validado.

---

## 2. Requisitos previos

- **Python >= 3.11** (probado en 3.11 y 3.13)
- **Node.js >= 18** (para `scripts/validate-data.mjs` y la validación de datos en CI)
- **Docker + Docker Compose** (opcional, recomendado para una demo reproducible)
- **API key LLM** (opcional): sin clave, el backend responde en **fallback determinista** cuando existe un escenario coincidente.

---

## 3. Instalación

Las dependencias se fijan con `pip-compile`: `*.in` contiene los rangos declarados y `*.txt` el lockfile reproducible.

```bash
# Backend + herramientas de calidad (tests, ruff, mypy, pip-audit)
pip install -r backend/requirements.txt -r dev-requirements.txt

# Frontend (Streamlit)
pip install -r requirements.txt
```

> Para cambiar una dependencia: edita el `.in` correspondiente y regenera el lockfile (ver [§8](#8-calidad-y-verificación)).

### Configuración

1. Copia la plantilla de entorno y completa los valores (nunca commitear `.env`):

   ```bash
   cp .env.example .env          # Linux/macOS
   Copy-Item .env.example .env   # Windows (PowerShell)
   ```

2. Variables principales:

| Variable | Descripción | Default |
|---|---|---|
| `APP_ENV` | Entorno (`development`/`production`) | `development` |
| `LOG_LEVEL` / `LOG_FORMAT` | Nivel y formato del log (`json`/`text`) | `INFO` / `json` |
| `LLM_PROVIDER` | Proveedor LLM (`groq`, `openai`, compatibles) | `groq` |
| `LLM_API_KEY` | Clave del proveedor | *(vacío → fallback)* |
| `LLM_MODEL` | Modelo | `openai/gpt-oss-20b` |
| `LLM_BASE_URL` | Base URL OpenAI-compatible (opcional) | vacío |
| `LLM_TIMEOUT_SECONDS` / `LLM_MAX_RETRIES` | Timeout y reintentos del proveedor | `25` / `1` |
| `PORT` | Puerto del backend | `3001` |
| `CORS_ORIGIN` | Orígenes permitidos (separados por coma) | `http://localhost:8501` |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | Límite de tasa de `/api/chat` | `true` / `30` / `60` |
| `MAX_HISTORY_MESSAGES` | Máximo de mensajes de `history` aceptados | `20` |
| `API_BASE_URL` / `API_TIMEOUT` | Backend que consume el frontend | `http://localhost:3001` / `60` |
| `FX_SOURCE` | Fuente de tasas (`demo`/`live`) | `demo` |

> El backend carga la configuración desde `.env` (raíz o `backend/.env`).

---

> ¿Solo frontend en la nube? Ver [Despliegue del frontend en Streamlit Community Cloud](docs/deploy-streamlit-cloud.md) (entrypoint: `streamlit_app.py` o `frontend/app.py`).

## 4. Ejecución local

### 4.1 Backend (FastAPI)

```bash
uvicorn backend.src.main:app --reload --port 3001
```

- Health: `GET http://localhost:3001/api/health` → `{ "status": "ok" }`
- Readiness: `GET http://localhost:3001/api/ready`
- Chat: `POST http://localhost:3001/api/chat`
- Documentación interactiva: `http://localhost:3001/api/docs`

### 4.2 Frontend (Streamlit)

```bash
streamlit run frontend/app.py
```

- App: `http://localhost:8501`
- Si el backend no está disponible, la UI muestra un **preview local** (ilustrativo, sin backend ni tools reales).

### 4.3 Docker Compose (demo reproducible)

```bash
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs -f backend frontend
docker compose down
```

- Backend: `http://127.0.0.1:3001` · Frontend: `http://127.0.0.1:8501`
- Por defecto `FX_SOURCE=demo` (determinista) y 2 workers de Uvicorn.
- No incluir `.env` ni secretos en las imágenes. La configuración de demo local no es un despliegue de producción.

---

## 5. API

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/health` | `GET` | Liveness del proceso (`{ "status": "ok" }`) |
| `/api/ready` | `GET` | Readiness: datos y dependencias críticas |
| `/api/version` | `GET` | Versión y entorno del servicio |
| `/api/chat` | `POST` | Simulación conversacional/estructurada |

**Request (`POST /api/chat`):** `message`, `context` (`amount_eur`, `destination_country`, `currency`, `fee_eur?`, `scenario_drop_pct?`, `project_budget?`), `history?`.

**Response (`200`):** `reply` y `agent` con `tools_used`, `reasoning_summary`, `scenarios`, `difference`, `assumptions`, `alerts`, `execution_mode`, `degraded`, `is_fallback`, `fx_source`, `fx_reference`, `calculation_source` y `budget_impact?`.

**Errores normalizados** (`{error, code, details}`):

| Código | Cuándo |
|---|---|
| `400` `invalid_input` / `BAD_REQUEST` | Mensaje vacío, corredor no soportado, comisión > importe, `history` excesivo |
| `422` `missing_data` / `UNPROCESSABLE` | Faltan datos mínimos (no se inventan cifras) |
| `429` `rate_limited` / `TOO_MANY_REQUESTS` | Se ha superado el límite de peticiones por cliente |
| `502` `upstream_failure` / `LLM_OR_TOOL_ERROR` | Fallo del LLM/tools (mensaje público sanitizado) |

**Cabecera de correlación:** toda respuesta incluye `X-Request-ID`; aparece también en los logs estructurados.

**Comportamiento clave:**

- El corredor soportado se lee de `data/processed/corridors.json` (matriz de cobertura en datos, no en código).
- Si falta `fee_eur` y existe regla para la moneda, se aplica la comisión de `data/processed/fee_rules.json`.
- Sin LLM o sin verificación completa, el sistema prioriza respuestas honestas: degradación sin escenarios no verificados o **fallback determinista** con `tools_used=[]`, `is_fallback=true`, `fx_reference=null`.
- `context.project_budget` se acepta; mientras el MVP no lo aplica, la respuesta incluye un `alert` explícito.

Detalle completo en [`docs/api-contract.md`](docs/api-contract.md) · [`shared/contracts/contracts.md`](shared/contracts/contracts.md).

---

## 6. Agente y herramientas

- **System prompt y diseño:** [`backend/src/agent/system_prompt.txt`](backend/src/agent/system_prompt.txt) · [`docs/agent-design.md`](docs/agent-design.md)
- **Tools (function calling, whitelist):**
  - `get_fx_reference(base, quote, date?)` → `{ rate, source, date, is_mock }`
  - `calculate_transfer_scenarios(amount_eur, rate, fee_eur, variations[], currency)` → escenarios, importes recibidos y diferencia
- **Guardrails:** el modelo no puede fijar importe, tasa, comisión, moneda ni variación; el backend los liga al contexto validado y a la tasa verificada.
- **Fuente de verdad demo:** `data/processed/` (tasas, reglas, corredores, presupuestos y escenarios golden). Ver [`data/README.md`](data/README.md).

---

## 7. Estructura del repositorio

```text
impact-fx/
├─ backend/                 # API FastAPI, orquestación LLM, tools y servicios
│  ├─ requirements.in/.txt  # rangos declarados + lockfile reproducible
│  └─ src/
│     ├─ agent/             # orquestador, prompt y esquemas de tools
│     ├─ api/               # rutas, middleware (request_id) y contrato de errores
│     ├─ config/            # configuración central por entorno
│     ├─ core/              # logging JSON, contexto, limitador de tasa
│     ├─ services/          # carga de datos con caché, impacto presupuestario
│     └─ tools/             # get_fx_reference, calculate_transfer_scenarios
├─ frontend/                # UI Streamlit (formulario, resultados, preview local)
├─ data/
│  ├─ raw/                  # fuentes originales (si aplica)
│  ├─ processed/            # fixtures/golden cases (fuente de verdad del MVP)
│  └─ schemas/              # esquemas de datos
├─ shared/contracts/        # contratos API/tools compartidos
├─ docs/                    # arquitectura, contrato, agente, benchmark, auditoría, ODS, demo
├─ scripts/                 # validación de datos, smoke, checks de entorno
├─ tests/                   # tests unitarios, de API HTTP y de servicios frontend
├─ pyproject.toml           # configuración de ruff, mypy, pytest y coverage
├─ .pre-commit-config.yaml  # hooks locales de calidad
├─ Dockerfile.backend / .frontend
└─ docker-compose.yml
```

---

## 8. Calidad y verificación

### Comandos

```bash
# Suite de tests (46 tests)
pytest tests -q

# Cobertura (umbral configurado en pyproject.toml: 60 %)
coverage run --source=backend,frontend -m pytest tests -q && coverage report

# Lint y formato
ruff check .
ruff format --check .

# Tipado estático
mypy backend

# Validación de datos
node scripts/validate-data.mjs

# Smoke test de la API (con el backend arrancado)
python scripts/smoke_backend.py

# Comprobación de entorno y LLM (opcional)
python scripts/check_env.py
```

### Puertas de calidad en CI (`.github/workflows/ci.yml`)

| Job | Qué garantiza |
|---|---|
| `validate` | Los datos procesados y los golden cases son coherentes |
| `lint` | `ruff check` + `ruff format --check` |
| `typecheck` | `mypy backend` sin errores |
| `backend-tests` | Tests + cobertura (≥ 60 %) en Python 3.11 y 3.13 |
| `backend-smoke` | El backend arranca y responde el caso B1 |
| `security` | `pip-audit` sobre los lockfiles (backend y frontend) |
| `docker-build` | Las dos imágenes se construyen correctamente |

Además: Dependabot (dependencias y acciones) y hooks locales con `pre-commit`.

### Regenerar los lockfiles

```bash
pip install pip-tools
pip-compile --strip-extras -o backend/requirements.txt backend/requirements.in
pip-compile --strip-extras -o requirements.txt requirements.in
pip-compile --strip-extras -o dev-requirements.txt dev-requirements.in
```

---

## 9. Documentación

| Área | Documentos |
|---|---|
| **Auditoría y escalado** | [Auditoría técnica y plan de escalado](docs/audit-escalado.md) |
| Producto y diseño | [Arquitectura](docs/architecture.md) · [Contrato API](docs/api-contract.md) · [Diseño del agente](docs/agent-design.md) · [Justificación ODS](docs/ods-justification.md) |
| Planificación | [Roadmap](docs/roadmap.md) · [Backlog](docs/backlog.md) · [Roles y tareas](docs/roles-tasks.md) · [Decision log](docs/decision-log.md) · [Pendientes del reto](docs/pendientes-reto.md) |
| Calidad y entrega | [Benchmark](docs/benchmark.md) · [Interacciones con razonamiento](docs/interactions.md) · [Guion de demo](docs/demo-script.md) · [Guía del día D](docs/day-of-execution-guide.md) |
| Técnica y operación | [Live FX](docs/live-fx.md) · [Workflow GitHub](docs/workflow-github.md) · [Deuda técnica](docs/tech-debt.md) · [Despliegue en Streamlit Cloud](docs/deploy-streamlit-cloud.md) |

---

## 10. Estado actual y limitaciones

- **Listo:** núcleo backend/frontend, tools deterministas, guardrails, metadatos trazables, fallback honesto, rate limiting, observabilidad básica, Docker, CI con puertas de calidad, tests y documentación.
- **Limitaciones conocidas:** corredor MVP acotado (EUR→KES), `context.project_budget` no se aplica todavía (se avisa en la respuesta), tasas de referencia (demo o Frankfurter) que no son cotización ejecutable, límite de tasa en memoria (por proceso) y sin persistencia ni identidad de usuario.
- **Siguiente paso:** plan por fases en [`docs/audit-escalado.md`](docs/audit-escalado.md) (métricas y trazas, caché de FX, rate limit compartido, presupuesto real, versionado de API).

---

## 11. Equipo (Grupo 1)

- **Juan Manuel** — Backend, API, LLM/orquestación
- **Laura** — Frontend, UX
- **Gema** — Agente, herramientas, prompt
- **José Melo** — Datos, integración, despliegue, demo y documentación

Mentores: Maya Petranova (técnica), Jesús Cal y Laura Mateus (ESG).

## Licencia

MIT. Ver [`LICENSE`](LICENSE).
