# Roadmap — Impact FX

## Visión
Entregar un MVP demostrable que cumpla todos los requisitos del reto: agente con decisión y herramientas, arquitectura cliente-servidor REST, respuesta integrada, ODS 9, 10 y 17 y entregables completos.

## Fases y cronograma

### Fase 0 — Descubrimiento y alineación (completada / confirmar)
- **Objetivo:** idea, ODS, equipo y problema.
- **Salida:** Impact FX elegido, ODS 9, 10, 17, Grupo 1 y roles propuestos.
- **Estado:** [x] Propuesto / [ ] Confirmado por el equipo.

### Fase 1 — Preparación (antes del jueves) — CRÍTICA
- **Objetivo:** llegar listos para construir (no para decidir).
- **Hitos:**
  - H1.1 Decisiones cerradas: stack, LLM+fallback (probado con tools), alcance Must, validación prompt/ODS con mentores.
  - H1.2 Repo y estructura listos, equipo con acceso.
  - H1.3 Datos procesados/validados + `demo_scenarios.json` (golden case).
  - H1.4 Contratos API/tools y esquemas congelados.
  - H1.5 System prompt (borrador final), spec de tools, docs base y benchmark listos.
  - H1.6 Boilerplate back/front arrancando, `.env.example`, deploy preparado.
- **Salida:** checklist de go/no-go en verde.
- **Ventana:** sesiones preparatorias + trabajo previo (hasta la víspera).

### Fase 2 — Ejecución día D (4–5 h de construcción)
- **Objetivo:** MVP integrado y verificado.
- **Hitos (timebox):**
  - H2.1 (T+00:20) Entorno arriba (`/health`, datos cargan).
  - H2.2 (T+01:30) Núcleo: 2 tools correctas, bucle tool-calling, UI operativa.
  - H2.3 (T+02:30) **Ciclo completo** end-to-end (caso Kenia) — *hito de control*.
  - H2.4 (T+03:15) B1–B3 en verde, respuesta integrada y manejo básico de errores.
  - H2.5 (T+04:00) URL desplegada (o plan B) y entregables documentales.
  - H2.6 (T+05:00) Ensayo demo y plan B verificado.
- **Salida:** MVP desplegado/funcional + docs + 3 interacciones.

### Fase 3 — Demo y evaluación (día D)
- **Objetivo:** demostrar valor y cumplimiento de requisitos.
- **Hitos:** presentación 8–10 min, ciclo completo en vivo, Q&A.
- **Salida:** evaluación del jurado/mentores.

### Fase 4 — Cierre y handover (post-reto)
- **Objetivo:** consolidar aprendizaje y dejar el proyecto mantenible.
- **Hitos:** registrar feedback, actualizar `decision-log.md` y `docs/tech-debt.md`, backlog de evolución.
- **Salida:** repo limpio y próximos pasos definidos.

### Fase 5 — Evolución (opcional, futuro)
- Adaptador de tasas reales (API) con fallback, más corredores, `assess_budget_impact` completo, tests automatizados, hardening de seguridad y observabilidad.

## Dependencias críticas (ruta crítica)
`Decisiones (stack/LLM)` → `Datos + Contratos congelados` → `Tools + Prompt + Backend LLM` / `UI` (paralelo) → `Integración (ciclo completo)` → `Benchmark` → `Deploy/Docs` → `Demo`.

## Hito de control (regla de oro)
Si al **T+02:30** no hay ciclo completo end-to-end: **congelar alcance** (cortar Should/Could/pulido/deploy) y dedicar el resto a integrar, verificar B1–B3 y asegurar una demo funcional (local si hace falta).
