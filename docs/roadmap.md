# Roadmap — Impact FX

## Visión
Entregar un MVP demostrable que cumpla los requisitos del reto: agente con decisión y herramientas, arquitectura cliente-servidor REST, respuesta integrada y trazable, ODS 9, 10 y 17 y entregables completos.

## Fases y cronograma

### Fase 0 — Descubrimiento y alineación
- **Objetivo:** idea, ODS, equipo y problema.
- **Salida:** Impact FX, ODS 9, 10, 17, roles.
- **Estado:** [x] Completado.

### Fase 1 — Preparación
- **Objetivo:** base técnica, datos, contratos y documentación.
- **Estado:** [x] Completado (base lista e integrada).
- **Hitos:**
  - [x] Decisiones de stack/LLM/fallback registradas.
  - [x] Repo/estructura, datos procesados y golden cases (`B1`, `B1b`, `B1c`).
  - [x] Contratos API/tools y esquemas definidos.
  - [x] System prompt, tools, backend/frontend MVP y artefactos Docker.

### Fase 2 — Ejecución (integración, hardening y verificación)
- **Objetivo:** MVP integrado, robusto y verificable.
- **Estado:** [~] En curso (hardening y verificación técnica avanzada completados; cierre E2E visual/despliegue pendiente).
- **Hitos:**
  - [x] Backend operativo (`/api/health`, `/api/chat`), CI (validate/tests/smoke), datos validados.
  - [x] Núcleo técnico: 2 tools deterministas, orquestación tool-calling, UI Streamlit operativa.
  - [x] Hardening: validación de procedencia FX/cálculo, metadatos (`fx_reference`, `is_fallback`, `budget_impact`), guardrails, B2/B3, errores 400/422/502 sanitizados, fallback determinista honesto.
  - [x] Pruebas: **38/38** unitarias/lógica + validación de golden cases; evidencias API B1–B3/fallback verificadas.
  - [ ] **Ciclo completo E2E con evidencia visual** (UI Streamlit + backend, capturas).
  - [ ] **E2E en Docker runtime** (`compose up/build`, health, chat/UI, logs) con evidencia.
  - [ ] **Validación con LLM real en entorno de demo final** y estabilidad de integración FE↔BE.
  - [ ] URL desplegada (o plan local validado) y entregables documentales cerrados con evidencias reales.
  - [ ] Ensayo de demo y plan B verificado.

### Fase 3 — Demo y evaluación
- **Objetivo:** demostrar valor y cumplimiento de requisitos.
- **Estado:** [ ] Pendiente.
- **Hitos:** presentación 8–10 min, ciclo completo en vivo, Q&A.

### Fase 4 — Cierre y handover
- **Objetivo:** consolidar aprendizaje y dejar el proyecto mantenible.
- **Estado:** [ ] Pendiente.
- **Hitos:** feedback, actualización de `decision-log.md` y `docs/tech-debt.md`, backlog.

### Fase 5 — Evolución (opcional)
- Tasas/cotizaciones reales ejecutables con fallback, más corredores, impacto por partidas con datos reales, observabilidad, E2E automatizado y hardening de seguridad.

## Dependencias críticas
`Datos + Contratos` → `Tools + Orquestador + UI` → `Hardening/Validación` → `E2E (UI/Docker/LLM real) + Evidencia` → `Deploy/Docs finales` → `Demo`.

## Estado resumido
- **Listo:** implementación MVP, hardening, trazabilidad, tests/CI y contratos actualizados.
- **Falta:** evidencia E2E visual/runtime (Docker/UI/entorno final), consolidación final de entregables y demo ensayada.