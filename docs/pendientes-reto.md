# Pendientes y estado — Impact FX (reto)

> **Estado (actualizado):** backend/API/LLM y hardening backend mergeados en `main` (PR #15, PR #22). La base técnica del MVP está implementada; queda completar integración end-to-end, despliegue y entregables con el equipo.

## Ya listo (verificado en repo / mergeado)
- [x] Backend FastAPI mergeado en `main`: `GET /api/health`, `POST /api/chat`, orquestación LLM + tool-calling, CORS y configuración por `.env` (PR #15).
- [x] Hardening backend mergeado en `main` (PR #22): 422 `missing_data` alineado al contrato, comisión por defecto desde `data/processed/fee_rules.json`, fallback determinista con mayor trazabilidad (motivo/alertas) y handler de validación para `/api/chat`.
- [x] Tools Python (`get_fx_reference`, `calculate_transfer_scenarios`) y artefactos de agente (`system_prompt.txt`, `tool_definitions.json`).
- [x] Fallback determinista desde `data/processed/demo_scenarios.json` cuando el LLM no está disponible/falla o se agotan rondas (si hay escenario coincidente).
- [x] Datos/contratos golden (`B1`, `B1b`, `B1c`, `B4`, `B5`) y validación de datos (`scripts/validate-data.mjs`).
- [x] Frontend Streamlit MVP (formulario, panel de resultados, consumo API y modo demo).
- [x] Pruebas y verificaciones disponibles: `tests/test_tools.py`, `tests/test_orchestrator.py`, `scripts/smoke_backend.py`, `scripts/check_env.py`.
- [x] CI en `main`: validación de datos, `backend-tests` (unit tests) y `backend-smoke`.
- [x] Probado con LLM real (Groq, modelo configurado en entorno de trabajo): el agente puede decidir y usar las 2 tools con cifras B1 correctas.
- [x] Documentación base y contratos actualizados (README, `docs/api-contract.md`, `shared/contracts/contracts.md`, docs de backend).

## Pendiente de integración y cierre (equipo)
- [ ] **Integración FE↔BE real**: `API_BASE_URL` apuntando al backend real, CORS correcto y verificación en UI (issue #9).
- [ ] **Validar ciclo integrado con LLM real** (no solo fallback/local): confirmar uso de tools y respuesta integrada en el flujo completo (issue #1).
- [ ] **Ajustar con el equipo** prompt/comportamiento del agente y manejo de errores 400/422/502 en casos reales; validar redacción/ámbito con mentores (D-009) (issue #5).
- [ ] **Pasar B1–B3 en flujo integrado** y capturar evidencias finales (issue #4).
- [ ] **Desplegar** backend y frontend, configurar variables de entorno/CORS y verificar URL(s) (issue #7).
- [ ] **Cerrar entregables**: README/doc técnica final según estado integrado, ≥3 interacciones reales con razonamiento, guion y ensayo de demo (issues #2 y #6).

## Notas de coordinación
- No tocar sin avisar: `data/processed/*`, `shared/contracts/*`, `docs/api-contract.md`, `backend/src/tools/*`, `backend/src/agent/system_prompt.txt`, `backend/src/agent/tool_definitions.json`.
- Cada persona mantiene su propio `.env` (no se commitea).
- Flujo Git: rama propia → PR a `main` con `Closes #N` → 1 aprobación.
- **Plan B demo:** si el LLM falla en vivo, el backend puede responder en fallback determinista (cuando haya escenario coincidente); validar este comportamiento en la integración.
