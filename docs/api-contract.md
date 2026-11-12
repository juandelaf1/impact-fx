# Contrato API — Impact FX

> **Estado:** congelado para el MVP. Cambios solo con acuerdo del equipo (D-007). Fuente compartida: [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md).

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
| `context.destination_country` | string (ISO 3166) | sí | País destino (ej. `KE`) |
| `context.currency` | string (ISO 4217) | sí | Moneda destino (ej. `KES`) |
| `context.fee_eur` | number (>=0) | no | Comisión en EUR (si falta, usar regla/supuesto) |
| `context.scenario_drop_pct` | number | no | Variación % escenario estrés (default 3) |
| `context.project_budget` | array | no | Partidas `[ {name, amount_local, priority?} ]` |
| `history` | array | no | Historial de mensajes (opcional MVP) |

#### Response 200
```json
{
  "reply": "Para un envío de 10.000 EUR a Kenia (KES) con una comisión de 40 EUR y una tasa de referencia de 145 KES/EUR (demo_reference, 2026-11-12, ficticia), el socio local recibiría 1.444.200 KES en el escenario base. Si la tasa cae un 3% (140,65 KES/EUR), recibiría 1.400.874 KES, es decir, 43.326 KES menos. Esta diferencia puede afectar partidas como transporte o suministros, por lo que conviene prever un margen.",
  "agent": {
    "tools_used": ["get_fx_reference", "calculate_transfer_scenarios"],
    "reasoning_summary": "Identificó monto, destino y comisión; obtuvo tasa de referencia y calculó escenarios base y -3% para integrar el impacto.",
    "fx_reference": { "rate": 145.0, "source": "demo_reference", "date": "2026-11-12", "is_mock": true },
    "is_fallback": false,
    "scenarios": [
      { "name": "base", "rate": 145.0, "fee_eur": 40, "amount_received": 1444200, "currency": "KES" },
      { "name": "stress_-3%", "rate": 140.65, "fee_eur": 40, "amount_received": 1400874, "currency": "KES" }
    ],
    "difference": { "amount": 43326, "currency": "KES" },
    "assumptions": [
      "Tasa de referencia ficticia (demo_reference, 2026-11-12, is_mock=true)",
      "Comisión fija 40 EUR (regla de demo)"
    ],
    "alerts": []
  }
}
```
| Campo | Tipo | Descripción |
|---|---|---|
| `reply` | string | Respuesta integrada en lenguaje claro (no output crudo de tools) |
| `agent.tools_used` | string[] | Herramientas ejecutadas |
| `agent.reasoning_summary` | string | Resumen breve de la decisión/flujo del agente |
| `agent.fx_reference` | object \| null | Referencia FX efectiva `{rate, source, date, is_mock}`; `null` si no se obtuvo una referencia |
| `agent.is_fallback` | boolean | `true` si responde el fallback determinista del orquestador; `false` en el flujo normal, incluido el fallback de la fuente FX |
| `agent.scenarios` | array | Escenarios calculados |
| `agent.difference` | object | Diferencia entre escenarios `{amount, currency}` |
| `agent.assumptions` | string[] | Supuestos explícitos (tasa/fuente/fecha/comisión) |
| `agent.alerts` | string[] | Alertas/impacto (p.ej. partidas afectadas) |

#### Errores
| HTTP | `code` | `error` | Cuándo |
|---:|---|---|---|
| 400 | `BAD_REQUEST` | `invalid_input` | Entrada inválida según validación del endpoint (p. ej. `message` vacío) |
| 422 | `UNPROCESSABLE` | `missing_data` | Faltan datos mínimos de simulación sin valor/regla inferible (p. ej. `currency`, `amount_eur`, `fee_eur` sin regla en `fee_rules.json`) o la request de chat no es procesable; el backend devuelve el detalle en `details` |
| 502 | `LLM_OR_TOOL_ERROR` | `upstream_failure` | Fallo no controlado del LLM/orquestación/tools en el endpoint |

Formato: `{ "error": "string", "code": "STRING", "details": "string" }`

## Notas de integración
- Frontend debe mostrar `reply` y, de forma estructurada, escenarios/diferencia/supuestos/`tools_used`/`alerts` (no el JSON crudo de las tools).
- Si falta `fee_eur` y existe regla para la moneda en `data/processed/fee_rules.json`, el backend puede aplicar la comisión por defecto antes de simular.
- En caso de 422, mostrar `details` (y `reply` si estuviera disponible) para solicitar/corregir el dato faltante.
- **Plan B / resiliencia:** si el LLM falla, no está disponible o se agotan rondas de tool-calling, el orquestador puede responder en **fallback determinista** desde `demo_scenarios.json` (cuando hay coincidencia), incluyendo motivo y alertas de trazabilidad en `agent`.
- `FX_SOURCE` es una variable de configuración (`demo`/`live`) que selecciona la fuente preferida. No es equivalente a `agent.fx_reference.source`, que identifica la fuente efectiva de la referencia usada; por ejemplo, una consulta live que degrada al fixture debe informar `source=demo_reference` e `is_mock=true`.
- **Brecha verificada (2026-11-12):** el backend actual todavía no devuelve `agent.fx_reference` ni `agent.is_fallback`; estos campos forman parte del contrato requerido y necesitan implementación/verificación con el responsable del backend.
