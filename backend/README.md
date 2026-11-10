# Backend — Impact FX

API REST y orquestación del agente (LLM + tools).

## Responsabilidades
- Exponer `GET /api/health` y `POST /api/chat`.
- Validar/sanitizar inputs y gestionar errores (400/422/502).
- Orquestar el LLM con *function calling* (system prompt + tools).
- Ejecutar tools contra `data/processed` e integrar resultados en la respuesta.
- Cargar configuración desde `.env` (nunca commitear claves).

## Estructura sugerida
```text
backend/src/
├─ api/        # rutas/controladores REST
├─ agent/      # prompt, bucle de tool-calling, composición de respuesta
├─ tools/      # get_fx_reference, calculate_transfer_scenarios, (assess_budget_impact)
├─ services/   # carga de datos, cálculos/validaciones
├─ config/     # env, cliente LLM, CORS
└─ index.*     # entrypoint
```

## Contratos
- API: [`../docs/api-contract.md`](../docs/api-contract.md)
- Tools y parámetros: [`../docs/agent-design.md`](../docs/agent-design.md), [`../shared/contracts/contracts.md`](../shared/contracts/contracts.md)

## Ejecución (completar según stack elegido)
```bash
# instalar dependencias
# configurar ../.env
# dev: npm run dev  |  uvicorn src.index:app --reload --port 3001
```

## Notas
- Fuente de verdad de datos: `../data/processed/`.
- Plan B: ante fallo LLM/red, responder con escenario determinista de `demo_scenarios.json` manteniendo el flujo.
- No exponer claves; validar inputs.
