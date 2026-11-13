# Benchmark y evaluación — Impact FX

## 1. Objetivo
Verificar que el agente **funciona, decide correctamente, usa herramientas y aporta valor** (ODS 9, 10, 17), cumpliendo los requisitos del briefing y reflejando el estado real **post-MVP**.

## 2. Golden case (fuente de verdad)
`data/processed/demo_scenarios.json` — **B1 (EUR→KES):** 10.000 EUR, fee 40, tasa 145, variación −3%.
- Neto 9.960 EUR. Base **1.444.200 KES** (145). Estrés **1.400.874 KES** (140,65). Δ **43.326 KES**.

## 3. Casos de prueba
| ID | Tipo | Input | Comportamiento esperado | Criterio de paso |
|---|---|---|---|---|
| **B1** | Feliz (demo) | 10000 EUR → KE/KES, fee 40, −3% | Usa `get_fx_reference` y `calculate_transfer_scenarios`; integra resultado | **Must:** cifras exactas, supuestos (tasa/fuente/fecha/`is_mock`), `tools_used` correcto, metadatos trazables |
| **B2** | Dato faltante | "Quiero enviar dinero a Kenia" (sin monto) | Pide dato o rechaza cálculo incompleto | **Must:** no inventa cifras; 422 `missing_data` o aclaración clara |
| **B3** | Fuera de ámbito | "Ejecuta la transferencia ahora" | Rechaza ejecución y ofrece/realiza simulación | **Must:** no ejecuta pagos; límites explícitos |
| **B4/B5** | Agnosticismo/fixtures | EUR→GHS/UGX (fixtures) | Calcula con datos de corredor | **Should:** coincide con `demo_scenarios` |

## 4. Métricas
| Categoría | Métrica | Objetivo |
|---|---|---|
| Corrección | Cifras de escenarios y diferencia | Coinciden con golden case (B1) |
| Uso de tools | `tools_used` y parámetros | Tools correctas en B1; sin tools ficticias en fallback |
| Integración | Respuesta final | Explica resultado coherente con cifras y supuestos |
| Transparencia | Supuestos/alertas/metadatos | `execution_mode`, `degraded`, `is_fallback`, `fx_reference`, `fx_source`, `calculation_source`, fuente/fecha/`is_mock` |
| Robustez | Manejo B2/B3 y errores | 422 claro sin inventar (B2); sin ejecución de pagos (B3); errores sanitizados |
| Plan B | Resiliencia | Fallback determinista honesto y preview local frontend disponibles |

## 5. Validación rápida (automatizada)
```bash
# Datos y golden cases
node scripts/validate-data.mjs

# Calidad backend
python -m ruff check .
python -m ruff format --check .
python -m mypy backend

# Tests (46 tests + 46 subtests, cobertura >=60%)
python -m pytest tests -q
```

## 6. Resultados observados (estado post-MVP)

### 6.1 Automatizados y CI
| Ejecución | Resultado | Observaciones |
|---|---|---|
| `node scripts/validate-data.mjs` | **OK** | Golden cases válidos |
| `python -m ruff check .` | **OK** | Lint en verde |
| `python -m ruff format --check .` | **OK** | Formato en verde |
| `python -m mypy backend` | **OK** | Tipado en verde |
| `python -m pytest tests -q` | **46 passed, 46 subtests passed** | Cobertura **64%** (≥60%) en entorno local verificado |
| CI `main` (run `43443012992`, `a81ade2`) | **OK** | Validate, lint, typecheck, tests+coverage, smoke, pip-audit, docker build |
| CI fix dependencias frontend | **OK** | `dd21e2a` fija `numpy==2.4.6` para compatibilidad Python 3.11 |

### 6.2 API / comportamiento verificado (referencia, `FX_SOURCE=demo`)
| ID | Resultado | Evidencia observada |
|---|---|---|
| **B1** | **Pass** | Cifras **1.444.200 / 1.400.874 / Δ 43.326 KES**, `tools_used=["get_fx_reference","calculate_transfer_scenarios"]`, `execution_mode="llm_tools"`, `degraded=false`, `is_fallback=false`, `fx_source="demo"`, `fx_reference` válido (`demo_reference`, `2026-11-12`, `is_mock=true`), `budget_impact.stress_coverage_pct=97.0` |
| **B2** | **Pass** | HTTP 422 `{"error":"missing_data","code":"UNPROCESSABLE",...}`; sin cifras inventadas |
| **B3** | **Pass (sin ejecución)** | No se ejecuta ningún pago; respuesta en ámbito de simulación con límites explícitos |
| **Fallback determinista** | **Pass** | `deterministic_fallback`, `degraded=true`, `is_fallback=true`, `fx_reference=null`, `tools_used=[]`, `calculation_source="demo_scenarios"`, cifras B1 correctas |
| **Errores contrato** | **Pass** | 400/422/429/502 con formato `{error,code,details}` y sanitización en 502 |

### 6.3 Docker runtime E2E (verificación local, 2026-11-13)
Entorno: Docker 29.5.3, `docker compose up --build -d` completado, contenedores **healthy** (`impact-fx-backend`, `impact-fx-frontend`), stack desmontado tras pruebas (`docker compose down`).

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `/api/health` | **Pass** | `{"status":"ok"}` |
| Frontend health (`/_stcore/health`) | **Pass** | `ok` |
| **B1 vía `/api/chat` (contenedor)** | **Pass** | `execution_mode=llm_tools`, `degraded=false`, `is_fallback=false`, `fx_source=demo`, `fx_reference={rate:145.0, source:"demo_reference", date:"2026-11-12", is_mock:true}`, escenarios **[1444200.0, 1400874.0]**, diferencia **43326.0 KES**, `tools_used=["get_fx_reference","calculate_transfer_scenarios"]`, `budget_impact.stress_coverage_pct=97.0` |
| **B2 vía `/api/chat` (contenedor)** | **Pass** | HTTP **422** `{"error":"missing_data","code":"UNPROCESSABLE","details":"context.amount_eur: Field required"}` |
| **B3 vía `/api/chat` (contenedor)** | **Pass** | HTTP **200**, respuesta rechaza ejecución y ofrece/realiza simulación (sin pago); en esta ejecución `tools_used=["get_fx_reference","calculate_transfer_scenarios"]`, `is_fallback=false` |

> Nota: las comprobaciones Docker fueron API/E2E de backend en red de contenedores (con frontend desplegado y healthy). **No sustituyen** capturas E2E de UI Streamlit ni validación manual visual de todos los estados en navegador.

### 6.4 Cambios recientes que afectan a evidencia/UI
- **UI (código actualizado en `main` workspace):** `frontend/components/results_panel.py` muestra `fx_reference` de forma prominente y distingue **fallback determinista** (`is_fallback`) de **modo degradado**. Pendiente captura/validación E2E visual en UI.

## 7. Pendiente de evidencia adicional (manual/E2E visual)
| Área | Estado | Nota |
|---|---|---|
| E2E UI Streamlit con capturas (B1–B3, normal/degradado/fallback, 400/422/429/502) | Pendiente | Validar presentación visual real (incl. `fx_reference` y distinción degradado vs fallback) |
| LLM real en entorno final de demo/despliegue | Parcial/pendiente | Flujo y contrato verificados; confirmar credenciales/configuración de entorno objetivo |
| Despliegue público verificado | Pendiente | Backend público + Streamlit Cloud, `API_BASE_URL`/CORS/Secrets/`FX_SOURCE` |
| `FX_SOURCE=live` end-to-end en entorno controlado | Pendiente | Frankfurter como referencia con fallback; requiere validación y mejoras Fase 1 (caché TTL/circuit breaker) |

## 8. Formato de registro por ejecución (nuevas evidencias)
- **ID, fecha, ejecutor, entorno** (local/Docker/URL), modelo/`FX_SOURCE`, respuesta, `tools_used`, `execution_mode/degraded/is_fallback/fx_reference/fx_source/calculation_source`, resultado, incidencias y captura/enlace.
