# Roadmap — Impact FX

## Visión
Entregar un MVP demostrable que cumpla todos los requisitos del reto: agente con decisión y herramientas, arquitectura cliente-servidor REST, respuesta integrada, ODS 9, 10 y 17 y entregables completos.

## Fases y cronograma

### Fase 0 — Descubrimiento y alineación
- **Objetivo:** idea, ODS, equipo y problema.
- **Salida:** Impact FX elegido, ODS 9, 10, 17, Grupo 1 y roles propuestos.
- **Estado:** [x] Completado.

### Fase 1 — Preparación (antes del jueves)
- **Objetivo:** llegar listos para construir (no para decidir).
- **Estado:** [~] Mayormente completada.
- **Hitos:**
  - [x] H1.1 Decisiones clave de stack/LLM/fallback tomadas y registradas (ver `decision-log.md`, D-003/D-004/D-010/D-012).
  - [x] H1.2 Repo y estructura listos, equipo con acceso.
  - [x] H1.3 Datos procesados/validados + `demo_scenarios.json` (golden cases).
  - [x] H1.4 Contratos API/tools y esquemas definidos y documentados.
  - [~] H1.5 System prompt, spec de tools, docs base y benchmark listos (pendiente validación final de prompt/ámbito con mentores, D-009).
  - [~] H1.6 Back/front y `.env.example` listos; despliegue preparado/pendiente de ejecución y verificación final.

### Fase 2 — Ejecución día D (integración y verificación)
- **Objetivo:** MVP integrado y verificado.
- **Estado:** [x] Completada (post-MVP; MVP/demo presentado ayer).
- **Hitos (timebox):**
  - [x] H2.1 Entorno backend operativo (`/health`, carga de datos, CI con validación/tests/smoke).
  - [x] H2.2 Núcleo técnico implementado: 2 tools, orquestación tool-calling, UI Streamlit operativa.
  - [x] H2.3 **Ciclo completo** end-to-end (caso Kenia) — verificado a nivel API/lógica y demo; evidencia UI/capturas finales pendiente de consolidar.
  - [x] H2.4 B1–B3 validados en contrato/lógica (B1 OK, B2 422 `missing_data`, B3 sin ejecución de pagos) y respuesta integrada con metadatos.
  - [~] H2.5 URL desplegada (o plan B) y entregables documentales cerrados — plan B/fallback disponible; despliegue público y cierre documental con evidencias finales pendientes.
  - [x] H2.6 Ensayo/demo y plan B verificado (demo presentada).
- **Salida:** MVP funcional con fallback/plan B, docs y contratos actualizados; evidencias E2E visuales/despliegue final por consolidar.

### Fase 3 — Demo y evaluación (día D)
- **Objetivo:** demostrar valor y cumplimiento de requisitos.
- **Estado:** [x] Completada (MVP presentado ayer).
- **Hitos:** presentación realizada, ciclo completo mostrado, Q&A (según sesión de demo).

### Fase 4 — Cierre y handover (post-reto)
- **Objetivo:** consolidar aprendizaje y dejar el proyecto mantenible.
- **Estado:** [~] En curso.
- **Hitos:** registrar feedback, actualizar `decision-log.md` y `docs/tech-debt.md`, consolidar evidencias/entregables y backlog de evolución.

### Fase 5 — Evolución (opcional, futuro)
- Adaptador de tasas reales (API) con fallback, failover entre proveedores LLM, más corredores, `assess_budget_impact` completo, tests automatizados, hardening de seguridad y observabilidad.

### Fase 6 — Profesionalización y escalado (2026-11-13 en adelante)
- **Objetivo:** convertir el MVP en un proyecto operable, reproducible y mantenible, y preparar el salto a producto.
- **Estado:** [~] Fase 0 completada; Fase 1 en planificación.
- **Hitos:**
  - [x] H6.1 Blindaje operativo: límite de tasa, `request_id`, logs JSON, sondas liveness/readiness/version.
  - [x] H6.2 Calidad automática: 46 tests, cobertura 40 %→64 %, ruff, mypy, pre-commit, CI con 7 jobs, `pip-audit`, Dependabot.
  - [x] H6.3 Reproducibilidad: lockfiles `pip-compile` (backend, frontend, dev) y Docker con usuario no root, workers y healthchecks.
  - [x] H6.4 Contrato documentado con las extensiones aditivas (429, `/api/ready`, `/api/version`, `X-Request-ID`) y deuda técnica actualizada.
  - [ ] H6.5 Observabilidad avanzada: métricas y trazas (OpenTelemetry + Prometheus) y alertas sobre tasa de `fallback`.
  - [ ] H6.6 Resiliencia: caché de FX con TTL y *circuit breaker*; límite de tasa compartido (Redis) para despliegue horizontal.
  - [ ] H6.7 Producto: aplicar el presupuesto real del usuario (`S1`) y versionado de API (`/api/v1`).
  - [ ] H6.8 industrialized: SBOM, escaneo de imágenes, `CHANGELOG`, releases y responsables reales en `CODEOWNERS`.
- **Detalle:** [`audit-escalado.md`](audit-escalado.md).

## Dependencias críticas (ruta crítica)
`Decisiones (stack/LLM)` → `Datos + Contratos congelados` → `Tools + Prompt + Backend LLM` / `UI` (paralelo) → `Integración (ciclo completo)` → `Benchmark` → `Deploy/Docs` → `Demo`.

## Hito de control (regla de oro)
Si al **T+02:30** no hay ciclo completo end-to-end: **congelar alcance** (cortar Should/Could/pulido/deploy) y dedicar el resto a integrar, verificar B1–B3 y asegurar una demo funcional (local si hace falta).
