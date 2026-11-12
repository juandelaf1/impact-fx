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

## 5. Modos de ejecución y trazabilidad

Estos modos no son intercambiables y deben registrarse por separado:

| Modo | Qué ocurre | Señal que debe mostrar la aplicación/API |
|---|---|---|
| **Normal** | LLM disponible; el agente ejecuta las tools y redacta la respuesta | `tools_used` refleja llamadas realmente ejecutadas; `is_fallback=false` |
| **Degradado de FX** | LLM disponible, pero falla la fuente FX seleccionada y `get_fx_reference` usa la tasa local | `FX_SOURCE` es la preferencia de configuración (`demo`/`live`); `fx_reference.source` describe el dato efectivamente usado. En degradación live→fixture, `source=demo_reference` e `is_mock=true`, aunque `FX_SOURCE=live` |
| **Fallback del agente** | El LLM falla o se agotan rondas; se usa un escenario coincidente de `demo_scenarios.json` | `is_fallback=true`; no atribuir tools que no se ejecutaron |
| **Demo local del frontend** | La UI no alcanza la API y genera una vista previa local | Banner **Demo preview**; no hubo petición procesada por backend ni ejecución de tools |

**Auditoría de implementación:** los contratos API y compartido ya documentan `agent.fx_reference` y `agent.is_fallback`, pero el backend actual no los devuelve. `FX_SOURCE` solo se lee como configuración en la tool; no hay un campo de respuesta `fx_source`. La respuesta normal incluye detalles de la tasa en `agent.assumptions`, no como referencia estructurada. La UI presenta un aviso de impacto general, no evalúa partidas presupuestarias concretas. Alinear estos puntos con Juan/Laura antes de considerar completa la trazabilidad estructurada.

## 6. Procedimiento de ejecución (día D)
1. Tras integración (T+02:30), ejecutar B1 desde UI y comparar con golden case.
2. Ejecutar B2 y B3; registrar comportamiento.
3. Capturar **≥3 interacciones** (recomendado: B1, B2, B3 o B6) con: petición, decisión/tools usadas, resultados relevantes y respuesta integrada → [`interactions.md`](interactions.md).
4. Si hay tiempo, ejecutar B4–B6.
5. Repetir smoke test en URL desplegada (o validar plan B local).

## 7. Estado de validación (2026-11-12)
- [x] Validación de datos y golden cases con `node scripts/validate-data.mjs`.
- [x] Build Compose y health checks de backend/frontend; la llamada desde el contenedor frontend al backend respondió correctamente.
- [x] B1 Compose: cifras exactas; una respuesta del agente reportó ambas tools. En una ejecución interactiva distinta, la UI solo reportó `get_fx_reference`; la selección de tools no fue reproducible en ambas llamadas.
- [x] B2 por API Compose: contexto sin importe devuelve 422.
- [x] B3 por API Compose: solicitud de pago real rechazada; no hay herramienta de pagos.
- [x] Demo local del frontend: al detener el backend, apareció “Demo preview” y se mostró la estimación ilustrativa.
- [x] Configuración Docker Compose validada con `docker compose config --quiet`.
- [x] Fallback determinista en Docker: cifras B1 correctas.
- [ ] B1 cumple todos los criterios: una ejecución del smoke test encontró ambas tools, pero las respuestas no incluyen `agent.fx_reference` ni `agent.is_fallback`; además, una ejecución UI solo reportó una tool.
- [ ] Fallback determinista informa `agent.is_fallback=true` y no atribuye tools no ejecutadas; ambas condiciones fallaron en el smoke test.
- [ ] B2/B3 desde la interfaz: la UI no permite enviar texto libre ni omitir el monto; las pruebas Compose fueron directas contra la API.
- [ ] Fallback de FX live→fixture comprobado de extremo a extremo; solo está cubierto por pruebas de la tool.
- [ ] Referencia FX y modo de ejecución disponibles como campos estructurados y mostrados en UI.
- [ ] Impacto presupuestario por partidas: no se pudo comprobar; la UI muestra solo una explicación general.
- [ ] Tres interacciones reales integradas registradas; los ejemplos I1–I3 de arriba son ilustrativos, no evidencia de ejecución.
