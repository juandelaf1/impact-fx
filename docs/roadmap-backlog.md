# Roadmap y Backlog — Impact FX

Este documento centraliza la planificación. Para detalle operativo usar:
- **Roadmap (fases e hitos):** [`roadmap.md`](roadmap.md)
- **Backlog priorizado (Must/Should/Could/Won’t):** [`backlog.md`](backlog.md)
- **Guía de ejecución día D (paso a paso):** [`day-of-execution-guide.md`](day-of-execution-guide.md)
- **Roles y tareas:** [`roles-tasks.md`](roles-tasks.md)
- **Decision log:** [`decision-log.md`](decision-log.md)
- **Benchmark y DoD:** [`benchmark.md`](benchmark.md)

## Resumen ejecutivo (post-MVP)
- **Estado:** MVP del reto **presentado** (post-demo). Núcleo funcional, contrato trazable, fallback honesto, hardening y Fase 0 de profesionalización integrados en `main`; CI en verde.
- **Logros clave:** 2 tools deterministas, corredor EUR→KES, ciclo completo y casos B1–B3 cubiertos a nivel de contrato/lógica, metadatos de ejecución (`execution_mode`, `degraded`, `fx_source`, `fx_reference`, `is_fallback`, `budget_impact`), Docker/CI/calidad reforzados.
- **Pendiente de cierre:** evidencias E2E con capturas, validación Docker runtime con evidencia, ajustes UI (`fx_reference` prominente, distinción degradado vs fallback), validación con LLM real en entorno final, despliegue público verificado y consolidación de entregables (`benchmark`, `interactions`, demo).
- **Próximo foco (Fase 1):** caché FX con TTL+circuit breaker, rate limit compartido (Redis), métricas/trazas, aplicar `context.project_budget` real, pruebas de carga, SBOM/digest y versionado `/api/v1` (ver `audit-escalado.md`, `roadmap.md`, `backlog.md`).
- **Plan B vigente:** fallback determinista backend (`demo_scenarios.json`) y preview local frontend (`frontend_demo`), sin fingir ejecución real.
