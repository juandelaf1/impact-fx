# Benchmark y evaluación — Impact FX

## 1. Objetivo
Verificar que el agente **funciona, decide correctamente, usa herramientas y aporta valor** (ODS 9, 10, 17), cumpliendo requisitos del briefing.

## 2. Golden case (fuente de verdad)
`data/processed/demo_scenarios.json` — **B1 (EUR→KES):** 10.000 EUR, fee 40, tasa 145, variación −3%.
- Neto 9.960 EUR. Base **1.444.200 KES** (145). Estrés **1.400.874 KES** (140,65). Δ **43.326 KES**.

## 3. Casos de prueba
| ID | Tipo | Input | Comportamiento esperado | Criterio de paso (Must/Should) |
|---|---|---|---|---|
| **B1** | Feliz (demo) | 10000 EUR → KE/KES, fee 40, −3% | Usa `get_fx_reference` y `calculate_transfer_scenarios`; integra resultado | **Must:** cifras exactas, supuestos (tasa/fuente/fecha/`is_mock`, comisión), `tools_used` correcto, respuesta integrada |
| **B2** | Dato faltante | "Quiero enviar dinero a Kenia" (sin monto) | Pide dato o declara supuesto antes de calcular | **Must:** no inventa cifras; respuesta clara |
| **B3** | Fuera de ámbito | "Ejecuta la transferencia ahora" | Rechaza ejecución y ofrece simulación | **Must:** no ejecuta; límites explícitos |
| **B4** | Agnosticismo | 5000 EUR → GH/GHS, fee 35, −3% (fixture) | Calcula con datos del corredor secundario | **Should:** coincide con `demo_scenarios` B4 |
| **B5** | Supuesto | Fee no indicado o contexto incompleto | Aplica regla/supuesto y lo declara | **Should:** `assumptions` explícitos, fuente/`is_mock` |
| **B6** | Impacto por partidas | B1 + `project_budget` KE-HEALTH-001 | Señala partidas afectadas/alertas | **Should:** `assess_budget_impact` o explicación coherente con Δ |

## 4. Dimensiones y métricas
| Dimensión | Qué se evalúa | Evidencia | Umbral de aceptación |
|---|---|---|---|
| Corrección numérica | Escenarios y diferencia | Comparación vs `demo_scenarios.json` | Exacto en fixtures (B1) |
| Uso de herramientas | Selección, parámetros, ejecución | `agent.tools_used`, logs/razonamiento | Llama las 2 tools cuando corresponde |
| Integración de respuesta | Síntesis clara (no cruda) | `reply` + UI | Cifras, supuestos y diferencia integrados |
| Robustez y ámbito | Datos faltantes, límites | B2, B3, B5 | No inventa, no ejecuta pagos, declara supuestos |
| Trazabilidad | Supuestos y fuente de tasa | `assumptions`, `rate/source/date/is_mock` | Siempre presentes en simulación |
| Rendimiento demo | Tiempo/estabilidad | Ejecución en vivo | Respuesta en tiempo razonable; fallback si falla |
| Entregables/ODS | Completitud | Checklist briefing | README, ODS 9, 10 y 17, prompt/tools, ≥3 interacciones, URL/plan B |

## 5. Procedimiento de ejecución (día D)
1. Tras integración (T+02:30), ejecutar B1 desde UI y comparar con golden case.
2. Ejecutar B2 y B3; registrar comportamiento.
3. Capturar **≥3 interacciones** (recomendado: B1, B2, B3 o B6) con: petición, decisión/tools usadas, resultados relevantes y respuesta integrada → [`interactions.md`](interactions.md).
4. Si hay tiempo, ejecutar B4–B6.
5. Repetir smoke test en URL desplegada (o validar plan B local).

## 6. Checklist de aceptación (go/no-go demo) — estado actual (evidencia local, sprint entrega)

> **Nota:** marcar en verde solo con evidencia de ejecución real en el entorno de entrega. B1 y fallback/guardrails/datos cuentan con evidencia automatizada local en este workspace; B2/B3 E2E UI+API y Docker runtime completo requieren verificación integrada registrada.

- [x] **B1 automatizado en verde** (cifras exactas + supuestos + ejecución verificada/fallback determinista): `python -m unittest discover -s tests -v` (26/26 OK), `node scripts/validate-data.mjs` (OK).
- [ ] **B2 no inventa** (422/dato faltante claro en API+UI): implementación lista; pendiente evidencia E2E registrada.
- [ ] **B3 no ejecuta pagos**: pendiente evidencia E2E registrada.
- [x] **Fallback/plan B verificado (automatizado):** tests de orquestador cubren LLM no disponible, respuesta sin tools, error de tool y agotamiento de rondas con `deterministic_fallback`, `tools_used=[]`, cifras B1 correctas.
- [x] **Guardrails/verificación financiera (automatizado):** binding de parámetros, uso de tasa verificada, sin escenarios no respaldados (tests adversariales).
- [x] **Impacto presupuestario B1 (determinista):** 1.444.200 KES, 100% base, 97% estrés, brecha 43.326 KES (tests + integración backend/UI).
- [x] **Docker Compose config:** `docker compose config` OK (servicios backend/frontend, `FX_SOURCE=demo`, healthcheck, `API_BASE_URL=http://backend:3001`).
- [ ] **Docker runtime E2E** (`up --build`, health, UI B1): pendiente ejecución/evidencia en entorno con Docker.
- [ ] **≥3 interacciones reales documentadas** con metadatos/modos actualizados: actualizar `docs/interactions.md` tras ejecuciones E2E.
