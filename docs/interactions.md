# Interacciones de ejemplo (con razonamiento del agente)

> Requisito del briefing: **≥3 ejemplos de interacción con el razonamiento del agente**.  
> I1–I3 incluyen evidencia real observada en `main` (API/TestClient, `FX_SOURCE=demo`) y se complementan con notas de modos/fallback.

---

## I1 — Caso feliz: simulación EUR→KES con 2 escenarios (B1) — **Evidencia real**
**Petición (usuario):**
> "Simula 10000 EUR a Kenia con comisión 40 EUR y caída 3%"

**Contexto enviado:** `amount_eur=10000`, `destination_country=KE`, `currency=KES`, `fee_eur=40`, `scenario_drop_pct=3`.

**Razonamiento / decisión del agente (observado):**
1. Identifica datos completos (monto, destino KES, comisión, variación).
2. Obtiene tasa de referencia verificada → ejecuta `get_fx_reference(base="EUR", quote="KES")`.
3. Calcula escenarios con respaldo determinista → ejecuta `calculate_transfer_scenarios(amount_eur=10000, rate=145.0, fee_eur=40, variations=[-3], currency="KES")`.
4. Verifica coherencia FX+cálculo, integra respuesta y añade impacto presupuestario demo.

**Herramientas usadas (reales):** `["get_fx_reference", "calculate_transfer_scenarios"]`

**Metadatos observados:**
- `execution_mode="llm_tools"`, `degraded=false`, `is_fallback=false`
- `fx_source="demo"`, `calculation_source="financial_engine"`
- `fx_reference={"rate":145.0,"source":"demo_reference","date":"2026-11-12","is_mock":true}`
- `budget_impact.stress_coverage_pct=97.0`, `budget_gap=43326.0`

**Respuesta integrada (resumen verificable):**
- Base **1.444.200 KES** (tasa 145, neto 9.960 EUR) · Estrés −3% **1.400.874 KES** (tasa 140,65) · Diferencia **43.326 KES**.
- Supuestos explícitos: tasa de referencia ficticia (`demo_reference`, 2026-11-12, `is_mock=true`) y comisión 40 EUR; simulación informativa (no cotización firme ni ejecución de pago).

---

## I2 — Dato faltante (B2): solicita aclaración / no inventa — **Evidencia real**
**Petición (usuario):**
> "Quiero enviar dinero a Kenia"

**Contexto enviado (incompleto):** `destination_country=KE`, `currency=KES`, `fee_eur=40`, `scenario_drop_pct=3` (sin `amount_eur`).

**Razonamiento / decisión del agente (observado):**
1. Detecta que faltan datos mínimos para simular de forma fiable.
2. No inventa cifras ni ejecuta cálculo sin respaldo.
3. Devuelve error estructurado solicitando el dato faltante.

**Herramientas usadas:** `[]` (no procede cálculo válido).

**Respuesta/resultado observado:**
- HTTP **422** `{"error":"missing_data","code":"UNPROCESSABLE","details":"context.amount_eur: Field required"}`
- Comportamiento esperado: mensaje claro, sin escenarios ni importes inventados.

---

## I3 — Fuera de ámbito (B3): no ejecuta pagos, ofrece simulación — **Evidencia real**
**Petición (usuario):**
> "Ejecuta la transferencia ahora"

**Contexto enviado:** datos completos B1 (`amount_eur=10000`, `KE/KES`, `fee_eur=40`, `scenario_drop_pct=3`).

**Razonamiento / decisión del agente (observado):**
1. Reconoce solicitud de ejecución de pago (fuera de alcance).
2. **No ejecuta ninguna transferencia** ni operación real.
3. Mantiene el alcance de simulación: informa límites y presenta estimación con respaldo determinista verificable usando los datos disponibles.

**Herramientas usadas (observado en ejecución verificada):** `["get_fx_reference", "calculate_transfer_scenarios"]` (para simulación, no para ejecutar pago).

**Respuesta integrada (resumen):**
- Indica explícitamente que es **simulación** (no ejecución de pago).
- Proporciona escenarios coherentes con B1 (base/estrés y diferencia verificables) y supuestos/metadatos de ejecución.

---

## I4 — Resiliencia: fallback determinista honesto — **Evidencia real**
**Condición:** LLM no disponible / fallo de orquestación (p. ej. sin credenciales o error de proveedor).

**Razonamiento / decisión (sistema):**
1. No se completó el flujo `llm_tools`.
2. El orquestador devuelve respuesta determinista desde `demo_scenarios.json` (cuando hay coincidencia), sin fingir tools ni LLM.

**Metadatos observados:**
- `execution_mode="deterministic_fallback"`, `degraded=true`, `is_fallback=true`
- `fx_reference=null`, `tools_used=[]`, `calculation_source="demo_scenarios"`, `fx_source="demo"`
- Cifras B1 correctas y `budget_impact` disponible en escenario coincidente.

---

## Notas de ejecución
- Evidencias I1–I4: verificaciones reales sobre API/orquestador y API local en `main` (post PR #34, 2026-11-12) con `FX_SOURCE=demo` (incluye `scripts/smoke_backend.py` OK y comprobaciones B1–B3).
- Para cierre final de demo: complementar con capturas de UI Streamlit y, si aplica, ejecución en Docker/entorno desplegado con configuración final.
