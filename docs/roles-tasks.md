# Roles, responsabilidades y tareas — Impact FX (Grupo 1)

## Equipo
| Persona | Rol principal | Backup | Foco |
|---|---|---|---|
| **Juan Manuel** | Backend & API / Integración LLM | Gema | Endpoints, cliente LLM, orquestación, validación, CORS, deploy back |
| **Laura** | Frontend & UX | José Melo | UI, formulario/validación, visualización de resultados, consumo API |
| **Gema** | Agente & Tools (IA) | Juan Manuel | System prompt, criterios de decisión, function calling, tools, integración de resultados |
| **José Melo** | Datos, Integración, Deploy & Demo/Docs | Laura | Fixtures/esquemas, contratos compartidos, integración, deploy, README/ODS/interacciones, benchmark y guion |

**Mentores (apoyo):** Maya Petranova (técnica), Laura Mateus (ESG/ODS), Jesús Cal.  
**QA/Benchmark:** responsabilidad transversal (coordina José Melo).

## Ownership (quién toca qué)
| Área | Owner | Artefactos |
|---|---|---|
| API y config backend | Juan Manuel | `backend/src/api`, `backend/src/config`, `.env.example` (runtime) |
| UI y experiencia | Laura | `frontend/` |
| Agente y herramientas | Gema | `backend/src/agent`, `backend/src/tools`, `docs/agent-design.md` |
| Datos y esquemas | José Melo | `data/`, `scripts/` |
| Contratos compartidos | José Melo + Gema/Juan | `shared/contracts/`, `docs/api-contract.md` |
| Docs, deploy y demo | José Melo | `docs/*`, `README.md`, despliegue |

> **Regla:** contratos y esquemas de datos **congelados**; cambios solo con acuerdo explícito y commit conjunto.

## RACI resumido
| Actividad | Juan | Laura | Gema | José |
|---|:---:|:---:|:---:|:---:|
| Decisión stack/LLM | R/A | C | R/A | C |
| Repo y estructura | C | C | C | R/A |
| Datos procesados/validados | C | I | C | R/A |
| Contratos API/tools | R | C | R | A |
| System prompt y criterios | C | I | R/A | C |
| Tools (implementación) | C | I | R/A | C |
| Endpoint + orquestación LLM | R/A | I | C | C |
| UI y consumo API | C | R/A | I | C |
| Integración end-to-end | R | R | R | R/A (coord.) |
| Benchmark y verificación | C | C | C | R/A |
| Deploy y URL | R | C | I | R/A |
| Documentación/entregables | C | C | R (agente) | R/A |
| Demo y presentación | R | R | R | R/A (coord.) |

`R` Responsable, `A` Aprueba/coordina, `C` Consultado, `I` Informado.

## Tareas por fase

### Preparación (antes del jueves) — completada
- **Juan Manuel:** boilerplate backend (`/health`, carga datos, cliente LLM por `.env`, esqueleto `/api/chat`), CORS/validación base, smoke *function calling*, preparación de despliegue.
- **Laura:** boilerplate frontend Streamlit (formulario, vista de escenarios/diferencia/supuestos, estados y consumo API), preparación de despliegue.
- **Gema:** system prompt, firmas JSON de tools, criterios de decisión, revisión de contratos/tools.
- **José Melo:** repo/estructura, `data/processed` + `demo_scenarios` validados, esquemas/contratos compartidos, documentación base, preparación de demo/deploy.
- **Todos:** roles confirmados, decisiones clave registradas y checklist revisado.

### Día D (4–5 h) — completado (MVP presentado)
- **Juan Manuel:** endpoint `/api/chat`, orquestación LLM+tools, errores/validación y hardening.
- **Laura:** UI conectada a API, presentación de resultados/supuestos/metadatos y estados.
- **Gema:** implementación/ajuste de tools y prompt, verificación de decisiones y respuestas integradas.
- **José Melo:** coordinación de integración, benchmark B1–B3, documentación/evidencias y guion/demo.
- **Todos:** integración end-to-end, pruebas y demo (plan B disponible).

### Post-MVP / cierre y escalado (actual)
- **Juan Manuel:** estabilidad backend/CI, fixes de compatibilidad/despliegue, soporte a Fase 1 (caché FX, rate limit compartido, métricas/trazas, versionado API) según backlog.
- **Laura:** ajustes UI pendientes (`fx_reference` prominente, distinción degradado vs fallback), validación E2E en Streamlit y capturas.
- **Gema:** validación/refinamiento de prompt y comportamiento del agente con LLM real en entorno final; apoyo en evidencias de interacciones.
- **José Melo:** consolidación de evidencias/entregables (`benchmark`, `interactions`, demo), despliegue/ensayo final y sincronización documental/proyecto.
- **Todos:** cerrar pendientes post-MVP, mantener contrato/datos como fuente de verdad y priorizar Fase 1 (`docs/audit-escalado.md`).

## Acuerdos de trabajo
- **Comunicación:** avisar bloqueos de inmediato; cambios de contrato/esquema solo con acuerdo.
- **Integración:** primer ciclo completo antes de pulir (hito T+02:30).
- **Commits:** pequeños y descriptivos (incluir evolución del agente/prompt).
- **Prioridad:** demo funcional y requisitos esenciales > extras. Si falta tiempo, seguir el orden de corte del backlog.
