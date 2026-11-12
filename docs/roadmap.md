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
- **Estado:** [~] En curso (backend y frontend base disponibles; integración final pendiente).
- **Hitos (timebox):**
  - [x] H2.1 Entorno backend operativo (`/health`, carga de datos, CI con validación/tests/smoke).
  - [x] H2.2 Núcleo técnico implementado: 2 tools, orquestación tool-calling, UI Streamlit operativa.
  - [ ] H2.3 **Ciclo completo** end-to-end (caso Kenia) — *hito de control*.
  - [ ] H2.4 B1–B3 en verde en flujo integrado, respuesta integrada y manejo de errores validado.
  - [ ] H2.5 URL desplegada (o plan B) y entregables documentales cerrados.
  - [ ] H2.6 Ensayo de demo y plan B verificado.
- **Salida esperada:** MVP desplegado/funcional + docs + ≥3 interacciones reales.

### Fase 3 — Demo y evaluación (día D)
- **Objetivo:** demostrar valor y cumplimiento de requisitos.
- **Estado:** [ ] Pendiente.
- **Hitos:** presentación 8–10 min, ciclo completo en vivo, Q&A.

### Fase 4 — Cierre y handover (post-reto)
- **Objetivo:** consolidar aprendizaje y dejar el proyecto mantenible.
- **Estado:** [ ] Pendiente.
- **Hitos:** registrar feedback, actualizar `decision-log.md` y `docs/tech-debt.md`, backlog de evolución.

### Fase 5 — Evolución (opcional, futuro)
- Adaptador de tasas reales (API) con fallback, failover entre proveedores LLM, más corredores, `assess_budget_impact` completo, tests automatizados, hardening de seguridad y observabilidad.

## Dependencias críticas (ruta crítica)
`Decisiones (stack/LLM)` → `Datos + Contratos congelados` → `Tools + Prompt + Backend LLM` / `UI` (paralelo) → `Integración (ciclo completo)` → `Benchmark` → `Deploy/Docs` → `Demo`.

## Hito de control (regla de oro)
Si al **T+02:30** no hay ciclo completo end-to-end: **congelar alcance** (cortar Should/Could/pulido/deploy) y dedicar el resto a integrar, verificar B1–B3 y asegurar una demo funcional (local si hace falta).
