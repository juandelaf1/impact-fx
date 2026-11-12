# Contrato API — Impact FX

> **Estado:** congelado para el MVP (cambios aditivos acordados y reflejados). Fuente compartida: [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md).

Base URL (local): `http://localhost:3001` (configurable por `PORT`). El frontend (Streamlit) usa `API_BASE_URL` para consumir la API.

## Endpoints

### 1) Health check
- **GET** `/api/health`
- **Response 200**
```json
{ "status": "ok" }
```

### 2) Chat / Simulación (agente)
- **POST** `/api/chat`
- **Headers:** `Content-Type: application/json`

#### Request body
```json
{
  "message": "Quiero enviar 10000 EUR a Kenia para un proyecto de salud",
  "context": {
    "amount_eur": 10000,
    "destination_country": "KE",
    "currency": "KES",
    "fee_eur": 40,
    "scenario_drop_pct": 3,
    "project_budget": [
      { "name": "Transporte y logística", "amount_local": 320000 }
    ]
  },
  "history": []
}
```
| Campo | Tipo | Req | Descripción |
|---|---|---:|---|
| `message` | string | sí | Mensaje del usuario |
| `context.amount_eur` | number (>0) | sí | Monto a enviar en EUR |
| `context.destination_country` | string (ISO 3166) | sí | País destino MVP: `KE` |
| `context.currency` | string (ISO 4217) | sí | Moneda destino MVP: `KES` |
| `context.fee_eur` | number (>=0) | no | Comisión en EUR (si falta, puede aplicar regla/supuesto definido) |
| `context.scenario_drop_pct` | number | no | Variación % escenario estrés (default 3) |
| `context.project_budget` | array | no | Partidas `[ {name, amount_local, priority?} ]`. Aceptado por contrato, pero **no aplicado** al cálculo de `budget_impact` en el MVP (se usa presupuesto demo fijo KE-HEALTH-001 cuando aplica). |
| `history` | array | no | Historial de mensajes (opcional MVP) |

#### Response 200
```json
{
  "reply": "Para un envío de 10.000 EUR a Kenia (KES) con una comisión de 40 EUR y una tasa de referencia de 145 KES/EUR (demo_reference, 2026-11-12, ficticia), el socio local recibiría 1.444.200 KES en el escenario base. Si la tasa cae un 3% (140,65 KES/EUR), recibiría 1.400.874 KES, es decir, 43.326 KES menos. Esta diferencia puede afectar la capacidad del proyecto para cubrir su presupuesto (cobertura estimada en estrés: 97%, brecha 43.326 KES, dato demo). Simulación informativa, no cotización firme ni ejecución de pago.",
  "agent": {
    "tools_used": ["get_fx_reference", "calculate_transfer_scenarios"],
    "reasoning_summary": "Obtuvo tasa de referencia verificada y calculó escenarios base y -3% con el motor determinista.",
    "scenarios": [
      { "name": "base", "rate": 145.0, "fee_eur": 40, "amount_received": 1444200.0, "currency": "KES" },
      { "name": "stress_-3%", "rate": 140.65, "fee_eur": 40, "amount_received": 1400874.0, "currency": "KES" }
    ],
    "difference": { "amount": 43326.0, "currency": "KES" },
    "assumptions": [
      "Tasa de referencia ficticia (demo_reference, 2026-11-12, is_mock=true)",
      "Comisión fija 40 EUR"
    ],
    "alerts": [],
    "execution_mode": "llm_tools",
    "degraded": false,
    "fx_source": "demo",
    "calculation_source": "financial_engine",
    "fx_reference": {
      "rate": 145.0,
      "source": "demo_reference",
      "date": "2026-11-12",
      "is_mock": true
    },
    "is_fallback": false,
    "budget_impact": {
      "project_id": "KE-HEALTH-001",
      "project_name": "Proyecto Salud Comunitaria — Kenia",
      "currency": "KES",
      "is_synthetic_demo": true,
      "budget_total": 1444200.0,
      "base_amount_received": 1444200.0,
      "stress_amount_received": 1400874.0,
      "base_coverage_pct": 100.0,
      "stress_coverage_pct": 97.0,
      "budget_gap": 43326.0,
      "budget_status": "partial"
    }
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `reply` | string | Respuesta integrada en lenguaje claro (no output crudo de tools) |
| `agent.tools_used` | string[] | Herramientas ejecutadas **correctamente** en esta respuesta (sin ejecuciones ficticias) |
| `agent.reasoning_summary` | string | Resumen breve de la decisión/flujo del agente o del modo degradado/fallback |
| `agent.scenarios` | array | Escenarios calculados (solo si hay respaldo determinista verificable) |
| `agent.difference` | object | Diferencia entre escenarios `{amount, currency}` |
| `agent.assumptions` | string[] | Supuestos explícitos (tasa/fuente/fecha/comisión, naturaleza ficticia/referencia) |
| `agent.alerts` | string[] | Alertas/impacto o avisos de degradación/límites |
| `agent.execution_mode` | string | `llm_tools` (flujo agente/LLM con tools) o `deterministic_fallback` (respuesta determinista sin flujo LLM completado). `frontend_demo` aplica solo en preview local del frontend (no lo emite el backend). |
| `agent.degraded` | boolean | `true` si la respuesta es degradada/fallback o no proviene del flujo completo esperado |
| `agent.fx_source` | string \| null | Categoría/procedencia FX: `demo` (fixtures/local ficticio o fallback demo), `frankfurter` (referencia externa) o `null` cuando no hay tasa FX verificada disponible (p. ej. degradado sin FX o cálculo no verificable). Independiente de `execution_mode`. |
| `agent.calculation_source` | string | Origen del cálculo: `financial_engine` (tools/cálculo determinista verificado), `demo_scenarios` (fixture/golden fallback), `frontend_preview` (solo frontend local, no backend) |
| `agent.fx_reference` | object \| null | Metadatos estructurados de la tasa cuando existen y son válidos: `{ rate, source, date, is_mock }`. `null` si no hay tasa verificada disponible (p. ej. fallback determinista). No se inventan metadatos. Su existencia **no** implica que existan escenarios financieros verificados. |
| `agent.is_fallback` | boolean | `true` solo si la respuesta procede del fallback determinista (`_fallback_response`); `false` en respuestas del flujo del agente (incluidas degradadas no redirigidas a fallback). |
| `agent.budget_impact` | object | (Opcional) Impacto presupuestario determinista demo cuando aplica (p. ej. KE-HEALTH-001). Puede incluirse en respuestas verificadas y en fallbacks deterministas con escenarios disponibles. No asigna déficit a partidas concretas y se marca como sintético/demo. **MVP:** se usa presupuesto demo fijo (KE-HEALTH-001); `context.project_budget` se acepta en la API pero **no** se aplica al cálculo de `budget_impact`. |

**Reglas de integración (congeladas):**
- `tools_used` contiene **solo** tools ejecutadas correctamente.
- `deterministic_fallback` nunca finge ejecución LLM ni tools no ejecutadas (`tools_used=[]`).
- `frontend_demo` nunca finge ejecución backend/tools reales.
- Solo una simulación con respaldo determinista verificable puede exponer `scenarios`/`difference` como resultados válidos.
- `reply` no debe contradecir las cifras estructuradas.
- Si `is_mock=true` o la tasa es de demo, debe comunicarse como ficticia/referencia; una tasa de Frankfurter es referencia externa, **no** cotización firme ni precio ejecutable.
- Distinguir: `execution_mode` (ejecución), `fx_source` (categoría/procedencia FX), `agent.fx_reference.source` (fuente concreta), `agent.is_fallback` (fallback determinista). `is_fallback` y `degraded` no son equivalentes.

#### Errores
Formato: `{ "error": "string", "code": "STRING", "details": "string" }`

| HTTP | `error` | `code` | Uso |
|---:|---|---|---|
| 400 | `invalid_input` | `BAD_REQUEST` | Mensaje vacío, corredor no soportado en MVP (usar KE/KES, EUR→KES) u otra entrada inválida |
| 422 | `missing_data` | `UNPROCESSABLE` | Faltan datos mínimos para simular (B2) o request no procesable; `details` claro, sin inventar cifras |
| 502 | `upstream_failure` | `LLM_OR_TOOL_ERROR` | Fallo interno/orquestación; `details` público sanitizado |

## Notas de integración
- Frontend debe mostrar `reply` y, de forma estructurada, escenarios/diferencia/supuestos/`tools_used`/`alerts`, metadatos de ejecución (`execution_mode`, `degraded`, `fx_source`, `calculation_source`, `fx_reference`, `is_fallback`) y `budget_impact` cuando exista, sin exponer JSON crudo de tools.
- Si falta `fee_eur` y existe regla para la moneda en `data/processed/fee_rules.json`, el backend puede aplicar la comisión por defecto antes de simular.
- **B2 (dato faltante):** priorizar respuesta `422 missing_data` con `details` claro; el frontend debe solicitar el dato faltante sin inventar cifras.
- **B3 (ejecución de pago):** el sistema no ejecuta pagos ni operaciones financieras reales; solo simula y debe comunicar límites.
- **Fallback determinista:** si el LLM falla/no está disponible o no se completa el flujo, el orquestador puede responder con `execution_mode=deterministic_fallback`, `degraded=true`, `is_fallback=true`, `calculation_source=demo_scenarios`, `fx_reference=null` y `tools_used=[]` (desde `demo_scenarios.json` cuando aplica), sin atribuir tools no ejecutadas.
- **Benchmark:** CI y golden case B1 con `FX_SOURCE=demo`; pruebas live con mocks y sin depender de tasas externas variables.
