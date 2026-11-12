# Guion de demo — Impact FX (8–10 minutos)

## Estructura y tiempos
| Bloque | Tiempo | Contenido | Responsable sugerido |
|---|---:|---|---|
| 1. Problema y ODS | 1:30 | Contexto: ONG envía fondos y no sabe cuánto llega; impacto en presupuesto/partidas. ODS 9, 10 y 17 | José / equipo |
| 2. Solución y diseño del agente | 2:00 | Qué hace Impact FX. Arquitectura (FE Streamlit / BE FastAPI REST). System prompt, 2 tools, guardrails y trazabilidad (`tools_used`, `fx_reference`, `is_fallback`, modos) | Gema / Juan |
| 3. Demo en vivo (núcleo) | 3:00 | Caso Kenia en la app/API: petición, ejecución de tools, escenarios, diferencia, supuestos/fuente, `budget_impact` y respuesta integrada | Laura (UI) + José (narración) |
| 4. Técnico y retos | 1:30 | Stack, contrato, datos deterministas, hardening/fallback honesto, Docker/CI y decisiones clave | Juan / Gema |
| 5. Aprendizajes y cierre | 1:00 | Aprendizajes y próximos pasos (tasas reales, más corredores) | Equipo |
| 6. Preguntas | 2:00 | Q&A | Todos |

## Guion detallado

### 1) Problema y ODS (1:30)
- "Cuando una ONG envía fondos al extranjero, presupuestar en euros no garantiza cuánto recibirá el socio local: el tipo de cambio y las comisiones pueden reducir el importe y afectar el proyecto."
- "Impact FX busca reducir esa desigualdad de información (ODS 10), mejorar coordinación con aliados (ODS 17) y aportar una herramienta digital transparente (ODS 9)."

### 2) Solución y diseño del agente (2:00)
- Flujo: usuario → `POST /api/chat` → agente (LLM + system prompt) **decide** → `get_fx_reference` y `calculate_transfer_scenarios` → verificación determinista → **respuesta integrada**.
- Trazabilidad: `tools_used` reales, `fx_reference` (rate/source/date/is_mock) o `null`, `execution_mode`/`degraded`/`is_fallback`, `fx_source`/`calculation_source`, supuestos y alertas.
- Límites: **no ejecuta pagos**; Frankfurter/tasas demo son referencia, no cotización firme ni precio ejecutable.

### 3) Demo en vivo (3:00) — caso B1 (verificado)
- **Entrada:** 10.000 EUR, destino Kenia (KES), comisión 40 EUR, variación −3%.
- **Narrar:** "El agente obtiene la tasa de referencia, calcula escenarios con el motor determinista y verifica coherencia antes de responder".
- **Mostrar (evidencia observada):**
  - `tools_used`: `get_fx_reference`, `calculate_transfer_scenarios`
  - `fx_reference`: `rate=145.0`, `source=demo_reference`, `date=2026-11-12`, `is_mock=true`
  - Base **1.444.200 KES**; estrés −3% **1.400.874 KES**; diferencia **43.326 KES**
  - `budget_impact` (demo KE-HEALTH-001): cobertura base 100%, estrés **97%**, brecha **43.326 KES** (sintético, sin atribuir a partidas)
  - `is_fallback=false`, `degraded=false`, `execution_mode=llm_tools`
- **Mensaje clave:** resultado verificable, trazable y honesto sobre supuestos/límites.

### 4) Técnico y retos (1:30)
- Stack: Streamlit + FastAPI + tools deterministas + LLM (tool-calling) y fallback determinista.
- Retos resueltos: coherencia contrato/metadatos, validación de procedencia FX y cálculos, manejo B2/B3/errores, y resiliencia sin fingir tools/LLM.
- Calidad: 38 tests unitarios/integración de lógica, validación de golden cases y CI (validate/tests/smoke).

### 5) Cierre (1:00)
- Aprendizajes: priorizar determinismo, trazabilidad y contratos claros.
- Evolución: más corredores/monedas, cotizaciones reales ejecutables (fuera de MVP), observabilidad y E2E automatizado.

## Casos de respaldo (evidencia disponible)
| Caso | Qué mostrar | Resultado observado |
|---|---|---|
| B2 (dato faltante) | "Quiero enviar dinero a Kenia" sin monto | HTTP 422 `missing_data` con detalle claro, sin cifras inventadas |
| B3 (fuera de alcance) | "Ejecuta la transferencia ahora" | No ejecuta pago; responde como simulación con límites explícitos (y puede incluir escenarios si hay datos) |
| Fallback determinista | LLM no disponible | `deterministic_fallback`, `degraded=true`, `is_fallback=true`, `fx_reference=null`, `tools_used=[]`, cifras B1 correctas |

## Plan B (si algo falla en vivo)
| Falla | Acción inmediata |
|---|---|
| LLM lento/cae o sin red | Mostrar fallback determinista del backend (mismo B1 verificable) o preview local frontend sin fingir backend/tools |
| Deploy caído / CORS | Cambiar a **demo local** (backend + frontend) |
| Error puntual en UI | Repetir petición, usar evidencia API capturada o `docs/interactions.md`/`docs/benchmark.md` |
| Docker daemon no disponible | Ejecutar localmente (`uvicorn` + `streamlit`) con `FX_SOURCE=demo` |

## Checklist previo a presentar
- [ ] Entorno (local/Docker/URL) probado con B1 (`FX_SOURCE=demo`).
- [ ] `.env` correcto, sin exponer claves en pantalla/logs.
- [ ] Números B1 verificados (1.444.200 / 1.400.874 / Δ 43.326 KES) y `budget_impact` (97% estrés, brecha 43.326 KES).
- [ ] Mostrar `tools_used`, `fx_reference`, `is_fallback`/metadatos y supuestos en UI o API.
- [ ] Capturas/evidencias E2E finales (UI y, si aplica, Docker) actualizadas.
- [ ] Plan B listo (fallback/local).