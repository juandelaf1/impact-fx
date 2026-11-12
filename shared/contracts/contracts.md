# Contratos compartidos (API y Tools)

> Contratos **congelados** para el MVP (cambios aditivos acordados). Fuente detallada: `docs/api-contract.md`.

## API REST

### `GET /api/health`
- **200**: `{ "status": "ok" }`

### `POST /api/chat`
**Request (JSON):**
```json
{
  "message": "Quiero enviar 10000 EUR a Kenia para un proyecto de salud",
  "context": {
    "amount_eur": 10000,
    "destination_country": "KE",
    "currency": "KES",
    "fee_eur": 40,
    "scenario_drop_pct": 3,
    "project_budget": [ { "name": "Transporte", "amount_local": 320000 } ]
  },
  "history": []
}
```
- `message` (string, req)
- `context` (object, req): `amount_eur` (number>0), `destination_country` (string), `currency` (string), `fee_eur` (number>=0, opc), `scenario_drop_pct` (number, opc, default 3), `project_budget` (array, opc)
- `history` (array, opc)

**Response 200 (JSON, campos principales):**
```json
{
  "reply": "Explicación integrada en lenguaje claro...",
  "agent": {
    "tools_used": ["get_fx_reference", "calculate_transfer_scenarios"],
    "reasoning_summary": "Obtuvo tasa de referencia y calculó escenarios base y -3%.",
    "scenarios": [
      { "name": "base", "rate": 145.0, "fee_eur": 40, "amount_received": 1444200.0, "currency": "KES" },
      { "name": "stress_-3%", "rate": 140.65, "fee_eur": 40, "amount_received": 1400874.0, "currency": "KES" }
    ],
    "difference": { "amount": 43326.0, "currency": "KES" },
    "assumptions": ["Tasa de referencia ficticia (demo_reference, 2026-11-12, is_mock=true)", "Comisión fija 40 EUR"],
    "alerts": [],
    "execution_mode": "llm_tools",
    "degraded": false,
    "fx_source": "demo",
    "calculation_source": "financial_engine",
    "fx_reference": { "rate": 145.0, "source": "demo_reference", "date": "2026-11-12", "is_mock": true },
    "is_fallback": false,
    "budget_impact": { "project_id": "KE-HEALTH-001", "stress_coverage_pct": 97.0, "budget_gap": 43326.0 }
  }
}
```

**Errores:**
- `400` `{ "error": "invalid_input", "code": "BAD_REQUEST", "details": "..." }`
- `422` `{ "error": "missing_data", "code": "UNPROCESSABLE", "details": "..." }` (faltan datos mínimos o request no procesable; B2 sin inventar cifras)
- `502` `{ "error": "upstream_failure", "code": "LLM_OR_TOOL_ERROR", "details": "..." }` (mensaje público sanitizado)

**Metadatos de ejecución (congelados, aditivos incluidos):**
- `execution_mode`: `llm_tools` | `deterministic_fallback` (backend). `frontend_demo` solo frontend.
- `degraded`: `true`/`false`.
- `fx_source`: `demo` | `frankfurter` | `null` (sin tasa FX verificada; independiente de `execution_mode`).
- `calculation_source`: `financial_engine` | `demo_scenarios` | `frontend_preview` (frontend).
- `fx_reference`: `{rate, source, date, is_mock}` | `null` (metadatos de tasa verificada; no implica escenarios verificados).
- `is_fallback`: `true` solo en fallback determinista; `false` en flujo del agente (aunque esté degradado).
- `budget_impact` (opcional): impacto presupuestario determinista demo cuando aplica.
- `tools_used`: solo tools ejecutadas correctamente; fallback determinista ⇒ `[]`.

**Notas de comportamiento:**
- Si falta `fee_eur` y existe regla para la moneda en `data/processed/fee_rules.json`, el backend puede aplicar la comisión por defecto.
- Fallback determinista: `execution_mode=deterministic_fallback`, `degraded=true`, `is_fallback=true`, `calculation_source=demo_scenarios`, `fx_reference=null`, sin fingir tools LLM.
- B3: no se ejecutan pagos reales; solo simulación.
- CI/golden B1 con `FX_SOURCE=demo`; live FX con mocks en tests. Frankfurter = referencia externa, no cotización firme ni precio ejecutable.

## Tools (function calling)

### `get_fx_reference`
- **Propósito:** obtener tasa de referencia para un par.
- **Input:** `{ "base": "EUR", "quote": "KES", "date?": "YYYY-MM-DD" }`
- **Output (éxito):** `{ "rate": 145.0, "source": "demo_reference", "date": "2026-11-12", "is_mock": true }`

### `calculate_transfer_scenarios`
- **Propósito:** calcular importe neto recibido por escenario y diferencia.
- **Input:** `{ "amount_eur": 10000, "rate": 145.0, "fee_eur": 40, "variations": [-3], "currency": "KES" }`
- Alcance MVP: `variations` debe contener exactamente una variación. `difference.amount` = importe base - importe escenario.
- **Output:** `{ "net_amount_eur": 9960.0, "scenarios": [...], "difference": { "amount": 43326.0, "currency": "KES" } }`

### `assess_budget_impact` (Should, opcional)
- **Input:** `{ "base_amount_received": 1444200, "stressed_amount_received": 1400874, "currency": "KES", "project_budget": [...] }`
- **Output:** `{ "affected_items": [...], "alerts": ["..."] }`
