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
  "reply": "Para un env?o de 10.000 EUR a Kenia (KES) con una comisi?n de 40 EUR y una tasa de referencia de 145 KES/EUR (demo_reference, 2026-11-12, ficticia), el socio local recibir?a 1.444.200 KES en el escenario base. Si la tasa cae un 3% (140,65 KES/EUR), recibir?a 1.400.874 KES, es decir, 43.326 KES menos. Esta diferencia puede afectar partidas como transporte o suministros, por lo que conviene prever un margen.",
  "agent": {
    "tools_used": ["get_fx_reference", "calculate_transfer_scenarios"],
    "reasoning_summary": "Identific? monto, destino y comisi?n; obtuvo tasa de referencia y calcul? escenarios base y -3% para integrar el impacto.",
    "scenarios": [
      { "name": "base", "rate": 145.0, "fee_eur": 40, "amount_received": 1444200, "currency": "KES" },
      { "name": "stress_-3%", "rate": 140.65, "fee_eur": 40, "amount_received": 1400874, "currency": "KES" }
    ],
    "difference": { "amount": 43326, "currency": "KES" },
    "assumptions": [
      "Tasa de referencia ficticia (demo_reference, 2026-11-12, is_mock=true)",
      "Comisi?n fija 40 EUR (regla de demo)"
    ],
    "alerts": [],
    "execution_mode": "llm_tools",
    "degraded": false,
    "fx_source": "demo",
    "calculation_source": "financial_engine"
  }
}
```
| Campo | Tipo | Descripci?n |
|---|---|---|
| `reply` | string | Respuesta integrada en lenguaje claro (no output crudo de tools) |
| `agent.tools_used` | string[] | Herramientas ejecutadas **correctamente** en esta respuesta (sin ejecuciones ficticias) |
| `agent.reasoning_summary` | string | Resumen breve de la decisi?n/flujo del agente o del modo degradado |
| `agent.scenarios` | array | Escenarios calculados (solo si hay respaldo determinista verificable) |
| `agent.difference` | object | Diferencia entre escenarios `{amount, currency}` |
| `agent.assumptions` | string[] | Supuestos expl?citos (tasa/fuente/fecha/comisi?n, naturaleza ficticia/referencia) |
| `agent.alerts` | string[] | Alertas/impacto o avisos de degradaci?n/l?mites |
| `agent.execution_mode` | string | `llm_tools` (LLM + tools ejecutadas) o `deterministic_fallback` (respuesta determinista sin flujo LLM completado). `frontend_demo` aplica solo en preview local del frontend (no lo emite el backend). |
| `agent.degraded` | boolean | `true` si la respuesta es degradada/fallback o no proviene del flujo completo esperado |
| `agent.fx_source` | string | Origen de la tasa usada: `demo` (fixtures/datos locales ficticios o fallback local) o `frankfurter` (referencia externa). Es independiente de `execution_mode`. |
| `agent.calculation_source` | string | Origen del c?lculo: `financial_engine` (tools/c?lculo determinista verificado), `demo_scenarios` (fixture/golden fallback), `frontend_preview` (solo frontend local, no backend) |

**Reglas de integraci?n (congeladas):**
- `tools_used` contiene **solo** tools ejecutadas correctamente.
- `deterministic_fallback` nunca finge ejecuci?n LLM ni tools no ejecutadas.
- `frontend_demo` nunca finge ejecuci?n backend/tools reales.
- Solo una simulaci?n con respaldo determinista verificable puede exponer `scenarios`/`difference` como resultados v?lidos.
- `reply` no debe contradecir las cifras estructuradas.
- Si `is_mock=true` o la tasa es de demo, debe comunicarse como ficticia/referencia; una tasa de Frankfurter es referencia externa, **no** cotizaci?n firme ni precio ejecutable.

Formato: `{ "error": "string", "code": "STRING", "details": "string" }`

## Notas de integración
- Frontend debe mostrar `reply` y, de forma estructurada, escenarios/diferencia/supuestos/`tools_used`/`alerts` y metadatos de ejecución (`execution_mode`, `degraded`, `fx_source`, `calculation_source`) sin exponer JSON crudo de tools.
- Si falta `fee_eur` y existe regla para la moneda en `data/processed/fee_rules.json`, el backend puede aplicar la comisión por defecto antes de simular.
- **B2 (dato faltante):** priorizar respuesta `422 missing_data` con `details` claro; el frontend debe solicitar el dato faltante sin inventar cifras ni rediseñar el flujo conversacional.
- **Plan B / resiliencia:** si el LLM falla, no está disponible o se agotan rondas de tool-calling, el orquestador puede responder en **fallback determinista** (`execution_mode=deterministic_fallback`, `degraded=true`, `calculation_source=demo_scenarios`) desde `demo_scenarios.json` cuando hay coincidencia, sin atribuir tools no ejecutadas.
- **Benchmark:** CI y golden case B1 deben ejecutarse con `FX_SOURCE=demo`; pruebas live deben usar mocks y no depender de tasas externas variables.

