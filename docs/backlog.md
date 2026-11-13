# Backlog — Impact FX

Backlog priorizado para lograr un MVP **viable y completo en 4–5 h** (con preparación previa hecha).  
Estados: `[ ]` pendiente · `[~]` en curso · `[x]` hecho · `[!]` bloqueado

> **Actualización (post-merge backend #15/#22):** componentes base y hardening backend están en `main`; los ítems pendientes se concentran en integración FE↔BE real, benchmark integrado, despliegue y entregables finales.
>
> **Actualización 2026-11-13 (profesionalización):** se abre la sección [Fase P — Profesionalización y escalado](#fase-p--profesionalización-y-escalado) con el trabajo de la auditoría (operación, calidad, reproducibilidad). Detalle en [`audit-escalado.md`](audit-escalado.md).

## Must — MVP (no negociable, día D)
| ID | Tarea | Responsable | Dependencias | Estado | Criterio de aceptación |
|---|---|---|---|---|---|
| M1 | Cerrar decisiones: stack, LLM principal+fallback (probado con tools), alcance Must | Equipo (Juan,Gema) | — | [x] | Decisiones registradas (D-003, D-004, D-010, D-012) y smoke/tool-calling probado |
| M2 | Repo + estructura + `.gitignore` + `.env.example` + docs base | José Melo | M1 | [x] | Estructura en repo, equipo con acceso, documentación base disponible |
| M3 | Datos procesados y validados (fx_rates, fee_rules, corridors, project_budgets, `demo_scenarios` EUR→KES) | José Melo | M2 | [x] | Golden cases en `data/processed/` y validador (`scripts/validate-data.mjs`) en verde |
| M4 | Contratos congelados: API (`/health`,`/chat`) y firmas de tools | Gema, Juan | M1 | [x] | `docs/api-contract.md` y `shared/contracts/` definidos (ajustes de alineación acordados documentados) |
| M5 | System prompt final (rol, ámbito ODS 9, 10, 17 + sensibilidad impacto/brecha, límites, criterios de decisión) | Gema | M1,M4 | [~] | Prompt implementado y documentado; pendiente validación final con mentores/equipo (D-009) |
| M6 | Implementar `get_fx_reference` (lee fixture, devuelve `rate,source,date,is_mock`) | Gema | M3,M4 | [x] | Tool implementada y cubierta por tests/golden cases |
| M7 | Implementar `calculate_transfer_scenarios` (base, variación, diferencia) | Gema | M3,M4 | [x] | Tool implementada y alineada con escenarios de referencia (B1 y otros) |
| M8 | Backend: `GET /api/health`, `POST /api/chat` con validación, cliente LLM y orquestación *function calling* | Juan | M4,M5,M6,M7 | [x] | Backend mergeado en `main` con orquestación, fallback determinista, manejo de errores y CI (tests + smoke) |
| M9 | Frontend: formulario, vista resultados (2 escenarios, diferencia, supuestos, `tools_used`), estados carga/error, consumo API real | Laura | M4 | [~] | UI Streamlit implementada; pendiente validación final contra backend real en todos los casos (incl. 422/alertas) y despliegue |
| M10 | Integración end-to-end (caso Kenia) | Todos | M8,M9 | [x] | Ciclo completo integrado documentado (PR #23); mantener verificación en entorno final de demo |
| M11 | Benchmark B1–B3 en verde y manejo básico de datos faltantes/ámbito | José (coord.), Gema, Juan | M10 | [x] | B1–B3 documentados en benchmark/interacciones (PR #23); confirmar evidencias finales en entorno de entrega |
| M12 | Despliegue (URL) o plan B local verificado; CORS/env correctos | José, Juan | M10 | [ ] | App accesible y operativa |
| M13 | Entregables documentales: README ejecutable, `ods-justification`, doc técnica (stack/endpoints/prompt/tools), **≥3 interacciones con razonamiento** | José, Gema | M10,M11 | [~] | Documentación técnica/README avanzados; faltan merge final de docs, evidencias integradas consolidadas y cierre de entregables |
| M14 | Guion de demo 8–10 min y ensayo | Todos (coord. José) | M12,M13 | [ ] | Demo fluida mostrando ciclo completo y plan B |

## Should — Solo si el Must está estable y desplegado
| ID | Tarea | Responsable | Dependencias | Estado | Criterio de aceptación |
|---|---|---|---|---|---|
| S1 | `assess_budget_impact` (alertas por partidas) | Gema | M10 | [ ] | Mapea diferencia a `project_budgets` y devuelve alertas coherentes |
| S2 | Manejo robusto de dato faltante/supuestos (422 + mensaje claro) | Juan, Gema | M10 | [ ] | B2 y casos sin fee/monto resueltos con claridad |
| S3 | 2º corredor precargado visible/verificable (agnosticismo) | José, Gema | M3,M10 | [ ] | B4 en verde con datos EUR→GHS |
| S4 | Benchmark B4–B6 completo | José | M11 | [ ] | Evidencia registrada |

## Could — Solo con todo lo anterior cerrado
| ID | Tarea | Responsable | Estado |
|---|---|---|---|
| C1 | Selector multi-corredor en UI | Laura | [ ] |
| C2 | Historial en sesión (cliente, sin BD) | Laura | [ ] |
| C3 | Few-shot ampliado en prompt | Gema | [ ] |
| C4 | Validación automática de datos en `scripts/` | José | [ ] |

## Won't (este reto)
- Ejecución real de pagos, login/usuarios, BD persistente.
- Scraping o tasas en tiempo real como dependencia de la demo.
- Múltiples agentes, cobertura global en vivo, gráficos complejos.

## Fase P — Profesionalización y escalado

> Ítems surgidos de la [auditoría técnica](audit-escalado.md) del 2026-11-13. No forman parte del entregable del reto, pero son la diferencia entre "funciona en mi máquina" y "es operable".

### P0 — Blindaje (completado)

| ID | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|
| P0.1 | Límite de tasa en `/api/chat` | [x] | `429 rate_limited` con `retry-after` implícito; configurable por entorno |
| P0.2 | Observabilidad: `request_id`, logs JSON, sondas | [x] | `X-Request-ID` en todas las respuestas; un log JSON por petición; `/api/health`, `/api/ready`, `/api/version` |
| P0.3 | Tests de la capa HTTP (400/422/429/502) | [x] | `tests/test_api.py`; cobertura de `api/routes.py` del 0 % al 82 % |
| P0.4 | Dependencias reproducibles (lockfiles) | [x] | `.in` + lockfiles `pip-compile`; suite verde en venv limpio |
| P0.5 | `pytest` operativo como estándar | [x] | `python -m pytest tests` funciona (antes fallaba la colección) |
| P0.6 | Puertas de calidad en CI | [x] | 7 jobs: datos, lint, tipado, tests+cobertura, smoke, `pip-audit`, Docker |
| P0.7 | Gestión de vulnerabilidades | [x] | `pip-audit` en CI + Dependabot |

### P1 — Operación y resiliencia (pendiente)

| ID | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|
| P1.1 | Métricas y trazas (OpenTelemetry → Prometheus) | [ ] | Latencia p50/p95, tasa de `fallback`, llamadas al LLM por petición |
| P1.2 | Caché de FX con TTL + *circuit breaker* | [ ] | Sin llamadas repetidas a Frankfurter; degradación limpia si el proveedor cae |
| P1.3 | Límite de tasa compartido (Redis) | [ ] | Límite efectivo con varias réplicas; misma interfaz `RateLimiter` |
| P1.4 | Presupuesto real del usuario (cierra `S1`) | [ ] | `context.project_budget` se aplica con reglas por prioridad y alertas por partida |
| P1.5 | Pruebas de carga (k6/Locust) | [ ] | Objetivos de latencia y coste por petición; verificación del límite de tasa |
| P1.6 | SBOM + escaneo de imágenes + digest de imagen base | [ ] | Artefactos de SBOM en CI; digest fijado de `python:3.11-slim` |
| P1.7 | Versionado de API (`/api/v1`) y política de deprecación | [ ] | Contrato versionado antes de abrir a terceros |

### P2 — Gobierno y documentación (pendiente)

| ID | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|
| P2.1 | `CODEOWNERS` con responsables reales | [ ] | Handles del equipo asignados por área |
| P2.2 | `CHANGELOG` y releases con tags semánticos | [ ] | Versiones publicadas y anotadas |
| P2.3 | Limpieza de ramas remotas obsoletas | [ ] | Solo ramas vivas en el remoto |
| P2.4 | Índice de documentación y estados sincronizados | [ ] | Backlog y docs reflejan el estado real del código |
| P2.5 | Tests de UI con `streamlit.testing.v1.AppTest` | [ ] | Cobertura de `frontend/app.py` y `results_panel.py` por encima del 0 % |

## Notas de gestión
- **Prioridad absoluta:** M10 (ciclo completo) > M11 > M12 > M13. Si hay retraso, cortar en orden: C* → S* → pulido visual → (último recurso) deploy (mantener demo local).
- **Congelados:** contratos y esquemas de datos (cambios solo con acuerdo del equipo).
- **Fuente de verdad numérica:** `data/processed/demo_scenarios.json`.
