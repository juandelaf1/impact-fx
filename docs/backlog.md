# Backlog — Impact FX

Backlog priorizado para lograr un MVP **viable y completo en 4–5 h** (con preparación previa hecha).  
Estados: `[ ]` pendiente · `[~]` en curso · `[x]` hecho · `[!]` bloqueado

> **Actualización (post-merge backend #15/#22):** componentes base y hardening backend están en `main`; los ítems pendientes se concentran en integración FE↔BE real, benchmark integrado, despliegue y entregables finales.

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

## Won’t (este reto)
- Ejecución real de pagos, login/usuarios, BD persistente.
- Scraping o tasas en tiempo real como dependencia de la demo.
- Múltiples agentes, cobertura global en vivo, gráficos complejos.

## Notas de gestión
- **Prioridad absoluta:** M10 (ciclo completo) > M11 > M12 > M13. Si hay retraso, cortar en orden: C* → S* → pulido visual → (último recurso) deploy (mantener demo local).
- **Congelados:** contratos y esquemas de datos (cambios solo con acuerdo del equipo).
- **Fuente de verdad numérica:** `data/processed/demo_scenarios.json`.
