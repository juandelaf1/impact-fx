# Impact FX — Reto Ebury + Fundación Somos F5 (Grupo 1)

Agente de IA que ayuda a ONG a estimar cuánto dinero recibe realmente su socio local en una transferencia internacional, comparando escenarios de tipo de cambio y comisiones e integrando el resultado en una respuesta clara.

- **ODS:** 9 (Industria, innovación e infraestructura), 10 (Reducción de las desigualdades) y 17 (Alianzas para lograr los objetivos).
- **Caso demo (MVP):** 10.000 EUR → Kenia (KES), comisión 40 EUR, tasa ref. 145 KES/EUR (ficticia, identificada), variación −3%.
  - Base: **1.444.200 KES** · Estrés (−3%): **1.400.874 KES** · Diferencia: **43.326 KES**.
- **Stack:** Frontend **Streamlit (Python)** · Backend **FastAPI (Python)** · Agente LLM con *function/tool calling* (Groq u OpenAI-compatible).

> **Alcance:** MVP simple y robusto (1 corredor principal, 2 escenarios, 2 tools). Agnóstico por diseño (datos por corredor), acotado en demo. No ejecuta pagos ni ofrece asesoría vinculante.

## Estructura del repositorio
```text
impact-fx/
├─ backend/                 # API REST (FastAPI), orquestación LLM y tools
├─ frontend/                # UI Streamlit (formulario + resultados)
├─ data/
│  ├─ raw/                  # fuentes originales (si aplica)
│  ├─ processed/            # fixtures listos para usar (fuente de verdad en demo)
│  └─ schemas/              # esquemas de datos
├─ shared/contracts/        # contratos API/tools compartidos
├─ docs/                    # arquitectura, agente, benchmark, ODS, demo, entregables
├─ scripts/                 # utilidades (smoke, validación de datos, checks)
└─ tests/                   # tests unitarios (tools/orquestador)
```

## Requisitos previos
- **Python >= 3.10** (recomendado 3.11)
- **Node.js >= 18** (para `scripts/validate-data.mjs` y validación de datos en CI)
- **Git**
- **(Opcional para modo LLM real)** API key de un proveedor con *function/tool calling* (p. ej. Groq, OpenAI o endpoint compatible). Sin API key, el backend puede responder en **modo fallback determinista** cuando hay un escenario coincidente en `data/processed/demo_scenarios.json`.

## Configuración
1. Clonar el repositorio y entrar en la carpeta del proyecto.
2. Copiar `.env.example` a `.env` en la raíz y completar los valores (nunca commitear `.env`).
   ```bash
   # Linux/macOS
   cp .env.example .env
   # Windows (PowerShell)
   Copy-Item .env.example .env
   ```
3. Variables principales:
   - **LLM:** `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` (opcional)
   - **Backend:** `PORT` (por defecto `3001`), `CORS_ORIGIN` (por defecto `http://localhost:8501`)
   - **Frontend:** `API_BASE_URL` (URL del backend, por defecto `http://localhost:3001`)

> La configuración del backend se carga desde `.env` (raíz o `backend/.env`).

## Ejecución local

### 1) Backend (FastAPI)
Desde la **raíz del repositorio** (recomendado):

```bash
pip install -r backend/requirements.txt
uvicorn backend.src.main:app --reload --port 3001
```

- Health: `GET http://localhost:3001/api/health` → `{ "status": "ok" }`
- Chat: `POST http://localhost:3001/api/chat`

### 2) Frontend (Streamlit)
En otra terminal, desde la raíz o desde `frontend/`:

```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```

- App: `http://localhost:8501`
- Consume `API_BASE_URL` (por defecto `http://localhost:3001`). Si el backend no está disponible, la UI puede mostrar un modo demo ilustrativo.

## API (resumen)
- `GET /api/health` → `{ "status": "ok" }`
- `POST /api/chat` → recibe `message`, `context` e `history`; el agente puede consultar tools y devuelve respuesta integrada:
  - `reply` (texto claro)
  - `agent.tools_used`, `agent.reasoning_summary`, `agent.scenarios`, `agent.difference`, `agent.assumptions`, `agent.alerts`

**Comportamiento relevante:**
- Si falta `fee_eur` y existe regla para la moneda, se aplica la comisión por defecto desde `data/processed/fee_rules.json`.
- Si faltan datos mínimos de simulación sin valor/regla, la API responde **422** (`missing_data` / `UNPROCESSABLE`).
- Errores de entrada: **400** (`invalid_input` / `BAD_REQUEST`).
- Fallos de LLM/tools no controlados en endpoint: **502** (`upstream_failure` / `LLM_OR_TOOL_ERROR`).
- Si el LLM falla o no está disponible, el orquestador puede devolver **fallback determinista** desde `demo_scenarios.json` (cuando hay coincidencia), incluyendo motivo/alertas de trazabilidad.

Detalle completo en [`docs/api-contract.md`](docs/api-contract.md) y [`shared/contracts/contracts.md`](shared/contracts/contracts.md).

## Agente y herramientas
- **System prompt y criterios:** [`backend/src/agent/system_prompt.txt`](backend/src/agent/system_prompt.txt), [`docs/agent-design.md`](docs/agent-design.md)
- **Tools (function calling, whitelist):**
  - `get_fx_reference(base, quote, date?)` → tasa de referencia desde fixtures (`rate`, `source`, `date`, `is_mock`)
  - `calculate_transfer_scenarios(amount_eur, rate, fee_eur, variations[], currency)` → escenarios, importes recibidos y diferencia
- **Datos de demo (fixtures):** `data/processed/` es la fuente de verdad para tasas, reglas, corredores y escenarios golden. Ver [`data/README.md`](data/README.md).

## Verificación y calidad

### Validación de datos
```bash
node scripts/validate-data.mjs
```

### Tests unitarios (backend/tools/orquestador)
```bash
pip install -r backend/requirements.txt
python -m unittest discover -s tests -v
```

### Verificación de entorno y LLM (opcional)
```bash
python scripts/check_env.py
```
Comprueba `.env`, conectividad con el modelo configurado y, si puede, un chat local de prueba.

### Smoke test de API
Con el backend arrancado en otra terminal:
```bash
python scripts/smoke_backend.py
```
Comprueba `/api/health`, el caso B1 (1.444.200 / 1.400.874 / Δ 43.326 KES) y el 400 con `message` vacío. Funciona también sin API key si el fallback determinista puede resolver el caso.

### CI
El workflow de GitHub Actions ejecuta:
- Validación de datos (`node scripts/validate-data.mjs`)
- Tests unitarios backend (`python -m unittest discover -s tests -v`)
- Smoke test backend (`uvicorn` + `python scripts/smoke_backend.py`)

## Documentación
**Empezar aquí (día D):** [Guía paso a paso día D](docs/day-of-execution-guide.md) · [Roadmap y backlog](docs/roadmap-backlog.md)

- **Producto y diseño:** [Arquitectura](docs/architecture.md) · [Contrato API](docs/api-contract.md) · [Diseño del agente](docs/agent-design.md)
- **Planificación:** [Roadmap](docs/roadmap.md) · [Backlog](docs/backlog.md) · [Roles y tareas](docs/roles-tasks.md) · [Decision log](docs/decision-log.md)
- **Calidad y entrega:** [Benchmark](docs/benchmark.md) · [Justificación ODS](docs/ods-justification.md) · [Guion demo](docs/demo-script.md)
- **Evidencias y seguimiento:** [Interacciones con razonamiento](docs/interactions.md) · [Deuda técnica](docs/tech-debt.md)

## Equipo (Grupo 1)
Juan Manuel (Backend/API & LLM), Laura (Frontend & UX), Gema (Agente & Tools), José Melo (Datos, Integración, Deploy & Demo/Docs).  
Mentores: Maya Petranova (técnica), Jesús Cal, Laura Mateus (ESG).

## Licencia
MIT. Ver [`LICENSE`](LICENSE).
