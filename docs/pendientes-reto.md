# Pendientes para el día del reto (jueves 12)

> Estado: backend preparado y verificado en `feat/1-backend-api-llm`. Esto es **preparación**; el trabajo de construcción e integración del MVP se hace en el evento.

## Ya listo (verificado)
- [x] App FastAPI arranca y responde `GET /api/health`.
- [x] `POST /api/chat` devuelve respuesta con `reply` + `agent{tools_used, scenarios, difference, assumptions, alerts, reasoning_summary}`.
- [x] Cifras del caso B1 verificadas: **1.444.200 / 1.400.874 / Δ 43.326 KES** (vía `scripts/smoke_backend.py`).
- [x] Validación de entrada: `message` vacío → 400.
- [x] Fallback determinista desde `data/processed/demo_scenarios.json` cuando el LLM no está disponible (probado sin API key).
- [x] Tools Python (`get_fx_reference`, `calculate_transfer_scenarios` con `currency`) y `system_prompt.txt` / `tool_definitions.json` (PR #12).
- [x] Frontend Streamlit MVP (PR #11): formulario, panel de resultados, consumo de la API y modo demo.
- [x] CI: validación de datos + smoke test del backend en cada PR a `main`.
- [x] Contratos, datos golden (`B1`, `B1b`, `B1c`, `B4`, `B5`) y documentación base.
- [x] **Probado con LLM real** (Groq `openai/gpt-oss-20b`): el agente decidió y llamó a `get_fx_reference` y `calculate_transfer_scenarios`, con cifras 1.444.200 / 1.400.874 / Δ 43.326 KES.
- [x] `tests/test_orchestrator.py`: 3 tests unitarios del bucle de tools (sin llamar al LLM).
- [x] `scripts/check_env.py`: verifica `.env`, conexión con el modelo y backend local.
- [x] PR #15 abierta (backend FastAPI), CI en verde, pendiente de 1 aprobación.

## Pendiente de integración (se hace el jueves, en equipo)
- [ ] **Conectar frontend ↔ backend reales**: `API_BASE_URL` apuntando al backend desplegado y verificación en la UI (issue #9).
- [ ] **Revisar y mergear la PR #15** (backend FastAPI): requiere 1 aprobación del equipo.
- [ ] **Probar el ciclo con LLM real** (no solo fallback): `.env` con `LLM_API_KEY` y `LLM_MODEL=openai/gpt-oss-20b`; comprobar que el agente **decide** y llama a las 2 tools (issue #1).
- [ ] **Ajustar con el equipo** el comportamiento del agente, el prompt y el manejo de errores (400/422/502) con datos reales (issue #5).
- [ ] **Pasar B1–B3 en el flujo integrado** y capturar evidencias finales (issue #4).
- [ ] **Validar el ámbito/prompt con mentores** (D-009) y ajustar la redacción (issue #5).
- [ ] **Desplegar** backend y frontend, configurar env/CORS y verificar la URL (issue #7).
- [ ] **Cerrar entregables**: README ejecutable, doc técnica final, ≥3 interacciones reales, guion y ensayo de demo (issues #2 y #6).

## Notas de coordinación
- No tocar sin avisar: `data/processed/*`, `shared/contracts/*`, `docs/api-contract.md`, `backend/src/tools/*`, `backend/src/agent/system_prompt.txt`, `backend/src/agent/tool_definitions.json`.
- Cada quien mantiene su propio `.env` (no se commitea).
- Flujo Git: rama propia → PR a `main` con `Closes #N` → 1 aprobación.
- Si el LLM falla en vivo: el backend cae en modo fallback determinista y la demo continúa.
