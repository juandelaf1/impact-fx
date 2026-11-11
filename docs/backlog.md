# Backlog — Impact FX

Backlog priorizado para lograr un MVP **viable y completo en 4–5 h** (con preparación previa hecha).  
Estados: `[ ]` pendiente · `[~]` en curso · `[x]` hecho · `[!]` bloqueado

## Must — MVP (no negociable, día D)
| ID | Tarea | Responsable | Dependencias | Estado | Criterio de aceptación |
|---|---|---|---|---|---|
| M1 | Cerrar decisiones: stack, LLM principal+fallback (probado con tools), alcance Must | Equipo (Juan,Gema) | — | [ ] | Decisiones en `decision-log.md` (D-003,D-004) y smoke test tools OK |
| M2 | Repo + estructura + `.gitignore` + `.env.example` + docs base | José Melo | M1 | [ ] | Estructura commiteada, equipo con acceso |
| M3 | Datos procesados y validados (fx_rates, fee_rules, corridors, project_budgets, `demo_scenarios` EUR→KES) | José Melo | M2 | [ ] | Golden case correcto (1.444.200 / 1.400.874 / Δ 43.326 KES) y esquemas coherentes |
| M4 | Contratos congelados: API (`/health`,`/chat`) y firmas de tools | Gema, Juan | M1 | [ ] | `docs/api-contract.md` y `shared/contracts/` acordados |
| M5 | System prompt final (rol, ámbito ODS 9, 10, 17 + sensibilidad impacto/brecha, límites, criterios de decisión) | Gema | M1,M4 | [ ] | Documentado en `docs/agent-design.md`; validado con mentores |
| M6 | Implementar `get_fx_reference` (lee fixture, devuelve `rate,source,date,is_mock`) | Gema | M3,M4 | [ ] | Retorna tasa EUR→KES correcta desde `fx_rates.json` |
| M7 | Implementar `calculate_transfer_scenarios` (base, variación, diferencia) | Gema | M3,M4 | [ ] | Coincide con `demo_scenarios.json` (B1) |
| M8 | Backend: `GET /api/health`, `POST /api/chat` con validación, cliente LLM y orquestación *function calling* | Juan | M4,M5,M6,M7 | [ ] | Llama al LLM, ejecuta tools y devuelve respuesta integrada + errores estandarizados |
| M9 | Frontend: formulario, vista resultados (2 escenarios, diferencia, supuestos, `tools_used`), estados carga/error, consumo API real | Laura | M4 | [ ] | UI funcional consumiendo `POST /api/chat`, sin hardcode de respuesta final |
| M10 | Integración end-to-end (caso Kenia) | Todos | M8,M9 | [ ] | Ciclo completo: input → decisión → 2 tools → respuesta integrada en UI |
| M11 | Benchmark B1–B3 en verde y manejo básico de datos faltantes/ámbito | José (coord.), Gema, Juan | M10 | [ ] | Cifras exactas; pide/supone dato faltante; rechaza ejecución de pagos |
| M12 | Despliegue (URL) o plan B local verificado; CORS/env correctos | José, Juan | M10 | [ ] | App accesible y operativa |
| M13 | Entregables documentales: README ejecutable, `ods-justification`, doc técnica (stack/endpoints/prompt/tools), **≥3 interacciones con razonamiento** | José, Gema | M10,M11 | [ ] | Cumple briefing; interacciones capturadas de ejecuciones reales |
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
