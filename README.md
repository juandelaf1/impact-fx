# Impact FX — Reto Ebury + Fundación Somos F5 (Grupo 1)

Agente de IA que ayuda a ONG a estimar cuánto dinero recibe realmente su socio local en una transferencia internacional, comparando escenarios de tipo de cambio y comisiones e integrando el resultado en una respuesta clara.

- **ODS:** 9 (Industria, innovación e infraestructura), 10 (Reducción de las desigualdades) y 17 (Alianzas para lograr los objetivos).
- **Caso demo (MVP):** 10.000 EUR → Kenia (KES), comisión 40 EUR, tasa ref. 145 KES/EUR (ficticia, identificada), variación −3%.
  - Base: **1.444.200 KES** · Estrés (−3%): **1.400.874 KES** · Diferencia: **43.326 KES**.
- **Stack:** Frontend **Streamlit (Python)**; Backend por confirmar (D-003).

> **Alcance:** MVP simple y robusto (1 corredor, 2 escenarios, 2 tools). Agnóstico por diseño (datos por corredor), acotado en demo. No ejecuta pagos ni ofrece asesoría vinculante.

## Estructura del repositorio
```text
impact-fx/
├─ backend/                 # API REST, orquestación del agente LLM y tools
├─ frontend/                # UI (formulario + resultados)
├─ data/
│  ├─ raw/                  # fuentes originales (si aplica)
│  ├─ processed/            # fixtures listos para usar (fuente de verdad en demo)
│  └─ schemas/              # esquemas de datos
├─ shared/contracts/        # contratos API/tools compartidos
├─ docs/                    # arquitectura, agente, benchmark, ODS, demo, entregables
└─ scripts/                 # utilidades (p.ej. validación de datos)
```

## Requisitos previos
- Python >= 3.10 (frontend Streamlit) y/o Node.js >= 18 según stack del backend elegido.
- Git.
- Una API key de un proveedor LLM con soporte de *function/tool calling* (p.ej. Groq, OpenAI, Gemini).

## Configuración
1. Clonar el repositorio y entrar en la carpeta del proyecto.
2. Copiar `.env.example` a `.env` y completar los valores (nunca commitear `.env`).
   ```bash
   cp .env.example .env
   ```
3. Variables clave: `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` (si aplica), `PORT`, `API_BASE_URL` (URL del backend para el frontend).

## Ejecución local
> Ajustar comandos al stack definitivo elegido por el equipo.

### Backend
```bash
cd backend
# instalar dependencias (npm install | pip install -r requirements.txt)
# ejecutar en desarrollo (npm run dev | uvicorn src.main:app --reload --port 3001)
```
- Health check: `GET http://localhost:3001/api/health`

### Frontend (Streamlit)
```bash
cd frontend
# crear entorno e instalar dependencias (pip install -r requirements.txt)
# ejecutar: streamlit run app.py
```
- App: `http://localhost:8501` (consume `API_BASE_URL`, por defecto `http://localhost:3001`).

## API (resumen)
- `GET /api/health` → `{ "status": "ok" }`
- `POST /api/chat` → recibe solicitud/contexto, el agente decide y ejecuta tools, devuelve respuesta integrada (`reply` + `agent.scenarios/difference/assumptions/tools_used`).

Detalle completo en [`docs/api-contract.md`](docs/api-contract.md).

### Verificación rápida
```bash
# 1. Arrancar la API
uvicorn backend.src.main:app --port 3001
# 2. En otra terminal
python scripts/smoke_backend.py
```
Comprueba health, el caso B1 (1.444.200 / 1.400.874 / Δ 43.326 KES) y el 400 con entrada inválida. Funciona sin API key (modo fallback determinista).

## Agente y herramientas
- **System prompt:** rol, ámbito (ODS 9, 10, 17; sensibilidad al impacto desigual), límites y criterios de decisión. Ver [`docs/agent-design.md`](docs/agent-design.md).
- **Tools (function calling):**
  - `get_fx_reference(base, quote, date?)` → tasa de referencia desde fixtures (`rate, source, date, is_mock`).
  - `calculate_transfer_scenarios(amount_eur, rate, fee_eur, variations[])` → escenarios, importes recibidos y diferencia.

## Datos
Los fixtures deterministas en `data/processed/` son la fuente de verdad para la demo (tasas ficticias identificadas). Ver [`data/README.md`](data/README.md).

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
Pendiente de definir por el equipo.
