# Contratos compartidos (API y Tools)

> Contratos **congelados** para el MVP. Cualquier cambio debe acordarse (evita romper la integración front-back-agente).

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

**Response 200 (JSON):**
```json
{
  "reply": "Explicación integrada en lenguaje claro...",
  "agent": {
    "tools_used": ["get_fx_reference", "calculate_transfer_scenarios"],
    "reasoning_summary": "Obtuvo tasa de referencia y calculó escenarios base y -3%.",
    "scenarios": [
      { "name": "base", "rate": 145.0, "fee_eur": 40, "amount_received": 1444200, "currency": "KES" },
      { "name": "stress_-3%", "rate": 140.65, "fee_eur": 40, "amount_received": 1400874, "currency": "KES" }
    ],
    "difference": { "amount": 43326, "currency": "KES" },
    "assumptions": ["Tasa de referencia ficticia (demo_reference, 2026-11-12, is_mock=true)", "Comisión fija 40 EUR"],
    "alerts": []
  }
}
```

**Errores:**
- `400` `{ "error": "invalid_input", "code": "BAD_REQUEST", "details": "..." }`
- `422` `{ "error": "missing_data", "code": "UNPROCESSABLE", "details": "..." }` (falta dato clave; el agente puede pedirlo en `reply`)
- `502` `{ "error": "upstream_failure", "code": "LLM_OR_TOOL_ERROR", "details": "..." }`

## Tools (function calling)

### `get_fx_reference`
- **Propósito:** obtener tasa de referencia para un par (desde fixtures).
- **Input:** `{ "base": "EUR", "quote": "KES", "date?": "2026-11-12" }`
- **Output:** `{ "rate": 145.0, "source": "demo_reference", "date": "2026-11-12", "is_mock": true }`

### `calculate_transfer_scenarios`
- **Propósito:** calcular importe neto recibido por escenario y diferencia.
- **Input:** `{ "amount_eur": 10000, "rate": 145.0, "fee_eur": 40, "variations": [-3], "currency": "KES" }`
- `currency`: moneda de destino obligatoria, expresada con tres letras (por ejemplo, `KES`). Debe corresponder a la tasa utilizada.
- Alcance MVP: `variations` debe contener exactamente una variación. `difference.amount` se calcula como importe base menos importe del escenario de variación.
- **Output:** `{ "net_amount_eur": 9960, "scenarios": [{ "name":"base","rate":145.0,"fee_eur":40,"amount_received":1444200,"currency":"KES" }, { "name":"stress_-3%","rate":140.65,"fee_eur":40,"amount_received":1400874,"currency":"KES" }], "difference": { "amount": 43326, "currency": "KES" } }`

### `assess_budget_impact` (Should, opcional)
- **Input:** `{ "base_amount_received": 1444200, "stressed_amount_received": 1400874, "currency": "KES", "project_budget": [...] }`
- **Output:** `{ "affected_items": [...], "alerts": ["..."] }`
