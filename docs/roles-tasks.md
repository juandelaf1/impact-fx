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

### Preparación (antes del jueves)
- **Juan Manuel:** boilerplate backend (`/health`, carga datos, cliente LLM por `.env`, esqueleto `/api/chat`), CORS/validación base, probar smoke test *function calling*, preparar despliegue back.
- **Laura:** boilerplate frontend (formulario + vista escenarios/diferencia/supuestos con mock), estados carga/error, servicio API, preparar despliegue front.
- **Gema:** system prompt (borrador final), firmas JSON de tools, criterios de decisión, plantilla de 3 interacciones, revisión de contrato de tools.
- **José Melo:** repo/estructura, `data/processed` + `demo_scenarios` validados, `data/README` y esquemas, contratos compartidos, docs base (arquitectura, benchmark, ODS, demo, tech-debt, roadmap/backlog/decision-log), preparar deploy.
- **Todos:** confirmar roles, cerrar D-003/D-004/D-009, revisar checklist go/no-go.

### Día D (4–5 h)
- **Juan Manuel:** endpoint `/api/chat` y orquestación LLM+tools, errores/validación, soporte deploy/CORS.
- **Laura:** UI final conectada a API real, presentación clara de escenarios/diferencia/supuestos/`tools_used`, estados.
- **Gema:** implementación `get_fx_reference` y `calculate_transfer_scenarios`, ajuste prompt, verificación de decisiones del agente y respuestas integradas.
- **José Melo:** coordinación de integración, ejecución benchmark B1–B3, deploy, README/ODS/doc técnica, captura de ≥3 interacciones, guion y tiempos de demo.
- **Todos:** integración end-to-end, pruebas, ensayo.

## Acuerdos de trabajo
- **Comunicación:** avisar bloqueos de inmediato; cambios de contrato/esquema solo con acuerdo.
- **Integración:** primer ciclo completo antes de pulir (hito T+02:30).
- **Commits:** pequeños y descriptivos (incluir evolución del agente/prompt).
- **Prioridad:** demo funcional y requisitos esenciales > extras. Si falta tiempo, seguir el orden de corte del backlog.
