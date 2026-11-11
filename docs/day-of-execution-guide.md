# Guía paso a paso — Día D (ejecución en 4–5 h para lograr el MVP)

Objetivo: terminar el día con un MVP **viable y completo** que cumpla los requisitos del reto (ciclo completo del agente, 2 tools, respuesta integrada, entregables y demo).

> **Regla de oro:** si al **T+02:30** no hay ciclo completo end-to-end, se congela el alcance (sin extras) y se prioriza integrar, verificar B1–B3 y asegurar la demo.

## Pre-requisitos (go/no-go antes de empezar el cronómetro)
- [ ] Repo clonado, todos con acceso y ramas listas.
- [ ] `.env` configurado en cada máquina (LLM con *tool calling* probado) y `.env` **no** commiteado.
- [ ] `data/processed/demo_scenarios.json` validado (Kenia: 1.444.200 / 1.400.874 / Δ 43.326 KES).
- [ ] Contratos API/tools y esquemas congelados (`docs/api-contract.md`, `shared/contracts/`).
- [ ] Back y front arrancan en local (aunque sea esqueleto); deploy preparado.
- [ ] Roles confirmados y guion de demo a mano.

---

## Cronograma detallado

### T+00:00–00:20 — Arranque y verificación (20 min)
**Objetivo:** entorno listo, sin sorpresas de base.
| Paso | Acción | Responsable | Hecho cuando |
|---:|---|---|---|
| 1 | `git pull` y crear/ubicar ramas de trabajo | Todos | Código y datos actualizados |
| 2 | Instalar dependencias back y front | Juan, Laura | Sin errores de instalación |
| 3 | Configurar `.env` local (copiar de `.env.example`) y verificar clave LLM | Juan, Gema | Variable cargada, no en git |
| 4 | Arrancar backend y comprobar `GET /api/health` | Juan | Responde `{ "status":"ok" }` |
| 5 | Arrancar frontend (Streamlit) y confirmar que carga (mock permitido en esta fase) | Laura | UI visible en navegador (`http://localhost:8501`) |
| 6 | Verificar que el back lee `data/processed/*` (rates/fees/corridors) | José, Juan | Datos accesibles |

**Salida del bloque:** entorno arriba. Si algo falla aquí, resolverlo ya (no arrastrar).

### T+00:20–01:30 — Núcleo en paralelo (70 min)
**Objetivo:** piezas listas para integrar (tools correctas, agente capaz de llamarlas, UI preparada).

**Pista A — Agente & Tools (Gema, apoyo Juan)**
| Paso | Acción | Hecho cuando |
|---:|---|---|
| A1 | Implementar `get_fx_reference(base, quote, date?)` leyendo `data/processed/fx_rates.json` | Devuelve `{rate,source,date,is_mock}` para EUR→KES |
| A2 | Implementar `calculate_transfer_scenarios(amount_eur, rate, fee_eur, variations[])` | Cálculo exacto: neto 9960, base 1.444.200, −3% 1.400.874, Δ 43.326 |
| A3 | Definir/ajustar **system prompt** (rol, ámbito ODS 9, 10, 17 + sensibilidad a impacto desigual/brecha según contexto, límites, criterios de decisión, obligación de declarar supuestos/fuente) | Prompt en `docs/agent-design.md` y cargado por el backend |
| A4 | Configurar definiciones de tools (JSON schema de parámetros) para *function calling* | LLM recibe las 2 tools con firmas correctas |

**Pista B — Backend & API (Juan, apoyo Gema)**
| Paso | Acción | Hecho cuando |
|---:|---|---|
| B1 | Implementar `POST /api/chat`: validar input, construir mensajes (system+user+context), llamar LLM, ejecutar tools solicitadas, devolver respuesta integrada | Endpoint responde con `reply` y `agent{tools_used,scenarios,difference,assumptions}` |
| B2 | Manejo básico de errores (400/422/502) y CORS | Errores claros; front puede llamar |
| B3 | Prueba local del endpoint (curl/Postman/UI) con caso B1 | Devuelve cifras del golden case |

**Pista C — Frontend (Laura, apoyo José)**
| Paso | Acción | Hecho cuando |
|---:|---|---|
| C1 | Formulario: `amount_eur`, destino (Kenia/KES), `fee_eur`, `scenario_drop_pct` + validación básica | Inputs controlados y validados |
| C2 | Vista de resultados: 2 escenarios, diferencia, supuestos/fuente/fecha/`is_mock`, `tools_used`, texto `reply` | Render claro (no JSON crudo) |
| C3 | Estados de carga y error; llamada a `POST /api/chat` usando `API_BASE_URL` | Lista para apuntar al back real |

**Coordinación (José):** vigilar contratos, resolver dudas de datos y preparar integración.

### T+01:30–02:30 — Integración end-to-end (60 min) **[HITO DE CONTROL]**
**Objetivo:** ciclo completo funcionando con el caso Kenia.
| Paso | Acción | Responsable | Hecho cuando |
|---:|---|---|---|
| 1 | Conectar front al back real (quitar mock de respuesta) | Laura, Juan | Petición llega y vuelve |
| 2 | Ejecutar caso B1 desde la UI: 10000 EUR, KE/KES, fee 40, −3% | Todos | Se muestra resultado en pantalla |
| 3 | Verificar ciclo completo: agente **decide** → llama `get_fx_reference` y `calculate_transfer_scenarios` → respuesta **integrada** | Gema, José | `tools_used` correcto, explicación coherente, cifras exactas |
| 4 | Ajustar bugs de integración (formato, CORS, parsing, tipos) | Juan, Laura, Gema | Flujo estable en 2 ejecuciones seguidas |
| 5 | **Decisión de corte:** si no hay ciclo completo al cierre del bloque → congelar alcance y dedicar lo que queda a integrar/verificar | José (coord.) | Alcance fijado |

**Salida del bloque:** demo interna del caso Kenia funcionando.

### T+02:30–03:15 — Calidad mínima y benchmark (45 min)
**Objetivo:** cumplir requisitos esenciales con comportamiento seguro.
| Paso | Acción | Responsable | Hecho cuando |
|---:|---|---|---|
| 1 | **B1:** cifras 1.444.200 / 1.400.874 / Δ 43.326 KES, supuestos visibles | José, Gema | En verde |
| 2 | **B2 (dato faltante):** pedir dato o declarar supuesto, sin inventar cifras | Gema, Juan | Respuesta clara |
| 3 | **B3 (fuera de ámbito):** “ejecuta el pago” → rechaza y ofrece simulación | Gema | Sin ejecución, límites explícitos |
| 4 | Mensajes de error/carga amigables en UI | Laura | UX comprensible |
| 5 | Capturar evidencias para **≥3 interacciones con razonamiento** (petición, decisión/tools, respuesta) | José | Material para `docs/interactions.md` |

### T+03:15–04:00 — Deploy y entregables (45 min)
**Objetivo:** entrega completa según briefing.
| Paso | Acción | Responsable | Hecho cuando |
|---:|---|---|---|
| 1 | Desplegar backend y frontend, configurar env/CORS en hosting, smoke test en URL | José, Juan | URL operativa (o activar plan B si falla en ≤20–30 min) |
| 2 | Completar `README.md` (instalación, `.env`, ejecución, uso, URL) | José | Reproducible |
| 3 | Cerrar `docs/ods-justification.md` (ODS 9, 10, 17 y aporte) | José | Justificación clara |
| 4 | Cerrar doc técnica: stack, endpoints, prompts, **system prompt**, descripción de cada tool (parámetros) | Gema, José | Requisito 5.1/entregable cubierto |
| 5 | Completar `docs/interactions.md` con ≥3 interacciones reales y razonamiento | José, Gema | Entregable cubierto |
| 6 | Commits finales descriptivos y push a `main` | Todos | Repo actualizado |

### T+04:00–05:00 — Colchón, ensayo y plan B (60 min)
**Objetivo:** demo sólida y resistente a fallos.
| Paso | Acción | Responsable | Hecho cuando |
|---:|---|---|---|
| 1 | Corregir fallos menores (solo si no rompen lo estable) | Según área | Sin regresiones |
| 2 | Verificar **plan B**: respuesta determinista desde `demo_scenarios.json` y/o demo local lista | Juan, José | Demo posible aunque falle LLM/red/deploy |
| 3 | Ensayo 8–10 min (problema/ODS → diseño agente → demo en vivo del ciclo → retos/aprendizajes) | Todos (coord. José) | Tiempos y turnos claros |
| 4 | Checklist final de entregables y DoD | José | Todo en verde |

---

## Checklist final (Definition of Done)
- [ ] Ciclo completo en vivo: input → decisión del agente → ≥2 tools → respuesta integrada (no cruda).
- [ ] Cifras Kenia correctas: 1.444.200 / 1.400.874 / Δ 43.326 KES, con supuestos (tasa, fuente, fecha, `is_mock`, comisión).
- [ ] Frontend consume backend real; estados de carga/error y validación básica.
- [ ] B1–B3 en verde.
- [ ] URL desplegada (o demo local + plan B) accesible.
- [ ] README, justificación ODS, doc técnica (stack, endpoints, prompts, system prompt, tools) y **≥3 interacciones con razonamiento** completos.
- [ ] Sin claves en el repo; `.env` fuera de git.

## Orden de corte ante falta de tiempo
1. Extras (Could) → 2. Should (`assess_budget_impact`, 2º corredor en UI, B4–B6) → 3. Pulido visual → 4. Deploy (si supera 20–30 min, pasar a demo local). **Nunca sacrificar:** ciclo completo, cifras correctas, respuesta integrada y entregables documentales mínimos.
