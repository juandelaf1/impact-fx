# Pendientes y estado — Impact FX (reto)

> **Estado (actualizado):** `main` integra el hardening del MVP (PR #32, PR #33): contrato/metadatos reforzados (`fx_reference`, `is_fallback`, `budget_impact`), validación de procedencia FX/cálculo determinista, fallback honesto, B2/422, B3 sin ejecución de pagos, Docker/CI y tests. La base técnica está implementada; quedan validación E2E con evidencia visual/despliegue y cierre documental final.

## Ya listo (verificado en repo / mergeado)
- [x] Backend FastAPI: `GET /api/health`, `POST /api/chat`, orquestación LLM + tool-calling, CORS y configuración por `.env`.
- [x] Tools deterministas (`get_fx_reference`, `calculate_transfer_scenarios`) y artefactos de agente (`system_prompt.txt`, `tool_definitions.json`).
- [x] Hardening orquestador/API: validación de `fx_reference` y verificación de escenarios contra motor determinista, guardrails financieros, invalidación ante FX/cálculo inválido, corrección `scenario_drop_pct=0`.
- [x] Metadatos de ejecución trazables: `execution_mode`, `degraded`, `fx_source`, `calculation_source`, `fx_reference`, `is_fallback`, `tools_used` reales; `budget_impact` determinista demo cuando aplica.
- [x] Fallback determinista honesto desde `demo_scenarios.json` (`deterministic_fallback`, `degraded=true`, `is_fallback=true`, `fx_reference=null`, `tools_used=[]`) sin fingir tools/LLM.
- [x] Manejo de errores: 400 `invalid_input`, 422 `missing_data` (B2, sin cifras inventadas), 502 sanitizado; B3 no ejecuta pagos.
- [x] Frontend Streamlit MVP: formulario, consumo API, preview local (`frontend_demo`), panel de resultados (escenarios, diferencia, supuestos, metadatos, `budget_impact`, alertas).
- [x] Datos y golden cases (`B1`, `B1b`, `B1c`, B4, B5) + `scripts/validate-data.mjs` OK.
- [x] Pruebas: `python -m unittest discover -s tests -v` → **38/38 OK**; `scripts/smoke_backend.py` disponible.
- [x] Docker: `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `.dockerignore`, `docker compose config` válido.
- [x] CI en verde (validate data, backend unit tests, backend smoke test) en PRs mergeadas.
- [x] Contratos compartidos y API actualizados con campos aditivos y semántica (`docs/api-contract.md`, `shared/contracts/contracts.md`).

## Evidencia verificada (API/lógica, `FX_SOURCE=demo`)
- [x] **B1:** 1.444.200 / 1.400.874 / Δ 43.326 KES, tools reales, `fx_reference` válido, `is_fallback=false`, `budget_impact` coherente.
- [x] **B2:** 422 `missing_data` con detalle claro, sin cifras inventadas.
- [x] **B3:** solicitud de ejecución rechazada en alcance (no se ejecuta pago), respuesta de simulación con límites.
- [x] **Fallback determinista:** respuesta honesta y verificable sin tools/LLM simulados.

## Pendiente de cierre (equipo)
- [ ] **E2E UI con capturas reales:** validar en Streamlit B1–B3, degradado vs fallback, visualización de `fx_reference`/`is_fallback`/`budget_impact` y mensajes 400/422/502.
- [ ] **E2E en Docker runtime:** `docker compose up --build -d`, health, chat B1, UI, logs y `down` con evidencia (depende de daemon/entorno).
- [ ] **Integración FE↔BE en entorno objetivo:** `API_BASE_URL`/CORS correctos y flujo completo validado.
- [ ] **Validación con LLM real en entorno de demo final:** confirmar estabilidad, uso de tools y respuesta integrada (además de fallback).
- [ ] **Despliegue (si aplica):** publicar URL(s), configurar variables/CORS y verificar.
- [ ] **Entregables finales:** actualizar/cerrar evidencias en `docs/benchmark.md` e `docs/interactions.md` con capturas reales, y confirmar `docs/demo-script.md`/README según estado final.
- [ ] **Revisión de higiene:** sin secretos en repo/logs/capturas; `.env` no commiteado.

## Notas de coordinación
- **No modificar sin acuerdo/justificación:** `data/processed/*` (fixtures/golden), `shared/contracts/*`, `docs/api-contract.md` (salvo cambios acordados), definiciones de tools.
- Cada persona mantiene su propio `.env` (no se commitea).
- Flujo Git: rama → PR a `main` → revisión/aprobación.
- **Plan B demo:** fallback determinista backend (`demo_scenarios.json`) y preview local frontend (`frontend_demo`) disponibles; no fingen ejecución real.