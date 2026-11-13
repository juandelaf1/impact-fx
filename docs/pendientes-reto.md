# Pendientes y estado — Impact FX (post-MVP)

> **Estado (actualizado 2026-11-13):** MVP/demo del reto **presentado (ayer)**. `main` integra el hardening del MVP (PR #32–#35, #37), la restauración de assets/entrypoint (PR #38/#39) y la profesionalización/escalado Fase 0 (PR #40) + fix de dependencias frontend para CI/Docker (commit `dd21e2a`). CI en `main` en verde. Queda cerrar evidencias finales (E2E/capturas/despliegue), ajustes de UI de equipo y avanzar Fase 1 de escalado.

## Completado (verificado en repo / `main`)
- [x] **Producto técnico MVP:** backend FastAPI (`/api/health`, `/api/ready`, `/api/version`, `/api/chat`), orquestación LLM + tool-calling, tools deterministas (`get_fx_reference`, `calculate_transfer_scenarios`), frontend Streamlit y preview local (`frontend_demo`).
- [x] **Contrato y trazabilidad:** `execution_mode`, `degraded`, `fx_source`, `fx_reference`, `is_fallback`, `calculation_source`, `tools_used` reales, `budget_impact` demo determinista cuando aplica; errores 400/422/429/502; correlación `X-Request-ID`.
- [x] **Comportamiento clave:** validación de procedencia FX/cálculo, fallback determinista honesto (`tools_used=[]`, `fx_reference=null`, `is_fallback=true`), B2 422 `missing_data` sin cifras inventadas, B3 sin ejecución de pagos, `scenario_drop_pct=0` corregido.
- [x] **Datos/golden cases:** `B1`, `B1b`, `B1c`, B4, B5 y `scripts/validate-data.mjs` OK.
- [x] **Calidad/operación (Fase 0):** 46 tests (+ subtests), cobertura 64%, `ruff`/`mypy`, lockfiles, CI reforzado (validate, lint, typecheck, tests+coverage, smoke, pip-audit, docker build), rate limiting, logging JSON, health/readiness/version, Dockerfiles/Compose endurecidos.
- [x] **Evidencia API/lógica verificada (referencia, `FX_SOURCE=demo`):** B1 (1.444.200 / 1.400.874 / Δ 43.326 KES, metadatos coherentes), B2 422, B3 en alcance, fallback determinista honesto.

## Pendiente de cierre (post-MVP)
- [ ] **E2E UI con capturas reales:** validar en Streamlit B1–B3, modos (normal/degradado/fallback), visualización de `fx_reference`/`is_fallback`/`budget_impact` y mensajes 400/422/429/502.
- [ ] **UI (equipo/Laura):** mostrar `fx_reference` de forma prominente y diferenciar claramente `degraded` (`is_fallback=false`) de fallback determinista en la interfaz.
- [ ] **E2E en Docker runtime con evidencia:** `docker compose up --build -d`, health, chat B1, UI, logs y `down` (cuando el daemon esté disponible).
- [ ] **Validación con LLM real en entorno final:** confirmar estabilidad, uso de tools y respuesta integrada (además de fallback).
- [ ] **Despliegue/entorno objetivo (si aplica):** backend público + Streamlit Cloud (`streamlit_app.py`/`frontend/app.py`) con `API_BASE_URL`/CORS/`FX_SOURCE`/LLM vars verificados.
- [ ] **Cierre documental/evidencias:** consolidar capturas y resultados reales en `docs/benchmark.md`, `docs/interactions.md`, `docs/demo-script.md` y README según estado final.
- [ ] **Higiene:** sin secretos en repo/logs/capturas; `.env` no commiteado.

## Escalado y evolución (ver `docs/audit-escalado.md` y backlog Fase P)
- [ ] **Fase 1:** caché FX con TTL + circuit breaker (P1.2/TD-11), rate limit compartido/Redis (P1.3), métricas/trazas (P1.1), aplicar `context.project_budget` real (S1/P1.4), pruebas de carga, SBOM/escaneo+digest, versionado `/api/v1`.
- [ ] **Live/FX:** integración `FX_SOURCE=live` (Frankfurter, referencia) existe con fallback; mejoras de resiliencia/gestión pendientes (no es cotización en tiempo real ejecutable).
- [ ] **Gobierno/docs:** sincronizar estados de backlog/roadmap, `CODEOWNERS` real, releases/CHANGELOG, limpieza de ramas/PRs obsoletas (p. ej. PR #36 conflictiva).

## Notas de coordinación
- **No modificar sin acuerdo/justificación:** `data/processed/*` (fixtures/golden), `shared/contracts/*` y `docs/api-contract.md` (salvo cambios aditivos acordados), definiciones de tools.
- Cada persona mantiene su propio `.env` (no se commitea).
- Flujo Git: rama → PR a `main` → revisión/aprobación.
- **Plan B demo:** fallback determinista backend (`demo_scenarios.json`) y preview local frontend (`frontend_demo`) disponibles; no fingen ejecución real.
