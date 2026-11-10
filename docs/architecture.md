# Arquitectura — Impact FX

## 1. Visión general
Impact FX es una aplicación web con **agente de IA** que simula el impacto de una transferencia internacional para ONG. Arquitectura **cliente-servidor** separada, comunicación por **API REST** JSON, diseño **agnóstico por datos** (corredores/reglas en configuración/fixtures) y demo acotada a 1 corredor (EUR→KES).

## 2. Componentes
| Componente | Responsabilidad | Tecnología (a confirmar, D-003) |
|---|---|---|
| **Frontend** (`frontend/`) | UI: formulario, estados, visualización de escenarios/diferencia/supuestos/alertas, consumo de API | React+Vite o HTML/JS (recomendado React+Vite) |
| **Backend** (`backend/`) | API REST, validación, orquestación del agente LLM, ejecución de tools, carga de datos | Node.js+Express o Python+FastAPI (recomendado Node.js+Express) |
| **Agente (LLM)** (`backend/src/agent`) | Interpretar petición, decidir herramientas (*function calling*), integrar resultados | Proveedor con tool calling (Groq/OpenAI/Gemini, D-004) |
| **Tools** (`backend/src/tools`) | Funciones deterministas invocadas por el agente | `get_fx_reference`, `calculate_transfer_scenarios` (+ `assess_budget_impact` Should) |
| **Datos** (`data/processed`) | Fixtures: tasas, comisiones, corredores, presupuestos, golden cases | JSON (fuente de verdad en demo) |
| **Contratos** (`shared/contracts`, `docs/`) | Especificación API y tools | Markdown/JSON |

## 3. Diagrama (flujo lógico)
```text
[Usuario / ONG]
      |
      v
[Frontend: Formulario + Resultados]
      |  POST /api/chat (message, context)
      v
[Backend: API REST]
      |  valida input
      v
[Agente / Orquestador LLM] <---- system prompt + definiciones de tools
      |  decide tool(s)
      v
[Tool: get_fx_reference] ----> [data/processed/fx_rates.json]
      |  {rate, source, date, is_mock}
      v
[Tool: calculate_transfer_scenarios] ----> [data/processed/fee_rules.json]
      |  {scenarios, difference}
      v
  (opcional Should) [assess_budget_impact] -> [project_budgets.json]
      |
      v
[Agente integra resultados] -> respuesta en lenguaje claro + supuestos
      |
      v
[Backend: Response JSON {reply, agent{...}}]
      |
      v
[Frontend: render escenarios, diferencia, supuestos, tools_used]
```

## 4. Flujo de petición (secuencia)
1. **Input:** usuario ingresa monto (EUR), destino/moneda (KES), comisión, variación (%) y opcionalmente partidas.
2. **Request:** Frontend envía `POST /api/chat` con `message`, `context`, `history`.
3. **Validación:** Backend valida/sanitiza (tipos, rangos, requeridos). Si falta dato crítico → `422` o el agente solicita/supone explícitamente.
4. **Decisión del agente:** LLM recibe system prompt + tools; decide llamar a `get_fx_reference` y/o `calculate_transfer_scenarios` según contexto.
5. **Ejecución de tools:** Backend ejecuta funciones con datos de `data/processed` y devuelve resultados al LLM.
6. **Integración:** Agente sintetiza respuesta (no cruda): explicación, escenarios, diferencia, supuestos (tasa/fuente/fecha/`is_mock`, comisión) y `tools_used`.
7. **Response:** Backend responde `{ reply, agent{tools_used, scenarios, difference, assumptions, alerts, reasoning_summary} }`.
8. **Render:** Frontend muestra comparación clara y estados (carga/error).

## 5. Contrato de API (resumen)
- `GET /api/health` → `200 { "status":"ok" }`
- `POST /api/chat` → request `{message, context{amount_eur,destination_country,currency,fee_eur,scenario_drop_pct,project_budget?}, history?}`; response `200 {reply, agent{...}}`; errores `400/422/502 {error,code,details}`.
- Detalle: [`api-contract.md`](api-contract.md) y [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md).

## 6. Diseño agnóstico por datos
- Corredores, tasas y comisiones parametrizados por `base/quote/country` en `data/processed` (no hardcode por país en lógica).
- Tools reciben parámetros genéricos (`base, quote`, `amount_eur, rate, fee_eur, variations`).
- **Demo acotada:** 1 corredor activo (EUR→KES); 1 secundario precargado en datos para evidenciar extensibilidad.

## 7. Seguridad y configuración
- API keys solo en `.env` (excluido de git); `.env.example` documentado.
- Validación/sanitización de inputs en backend (y básica en frontend).
- CORS restringido al origen del frontend.
- Sin ejecución de pagos ni acceso a sistemas bancarios; datos de demo curados/sintéticos.

## 8. Resiliencia y plan B
- **Fuente primaria de tasas:** fixtures locales (determinismo).
- **Fallback:** si falla LLM/red, modo determinista usando `demo_scenarios.json` (manteniendo el flujo visible) y/o demo local.
- **Deploy:** FE/BE en plataformas PaaS; si falla, demo local (priorizar demo funcional).

## 9. Decisiones relacionadas
Ver [`decision-log.md`](decision-log.md): D-002 (alcance), D-003 (stack), D-004 (LLM), D-005/D-006 (datos), D-007 (contratos), D-008 (tools), D-010 (plan B).
