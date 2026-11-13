# Auditoría técnica y plan de escalado — Impact FX

> **Fecha:** 2026-11-13 · **Alcance:** repositorio completo (backend FastAPI, agente LLM con tools, frontend Streamlit, datos, CI, Docker, documentación).
> **Método:** lectura del código y la documentación, ejecución de la suite de tests, medición de cobertura, lint y tipado, instalación limpia de las dependencias fijadas y ejecución de la suite en un entorno virtual nuevo.

---

## 1. Resumen ejecutivo

**Veredicto:** el proyecto es un **MVP sólido y honesto**, pero **no está preparado para escalar tal como está**. La lógica de negocio es buena (motor determinista con `Decimal`, verificación de procedencia de la tasa, *fallback* honesto que no finge ejecuciones), el contrato API está documentado y congelado, y la trazabilidad (`execution_mode`, `degraded`, `fx_source`, `is_mock`) es un activo real del producto.

El problema no es la calidad del núcleo: es la **falta de capacidades de operación** alrededor de él. Sin límite de tasa, sin observabilidad, sin tests de la capa HTTP, sin dependencias reproducibles ni puertas de calidad en CI, cualquier despliegue real del proyecto se traduce en: gasto de API no controlado, incidencias sin diagnóstico, builds no reproducibles y degradación silenciosa.

### Puntuación por dimensión (0-5)

| Dimensión | Antes | Ahora | Comentario |
|---|:--:|:--:|---|
| Núcleo funcional / dominio | 4.5 | 4.5 | Motor determinista y contrato bien pensée. Sin cambios relevantes. |
| Seguridad | 1.5 | 3.0 | Rate limiting y cabeceras de correlación añadidos. Falta autenticación y cifrado en tránsito. |
| Observabilidad | 1.0 | 3.0 | Logs JSON + `X-Request-ID`. Falta métricas, trazas y alertas. |
| Calidad automática (tests) | 2.0 | 3.5 | 46 tests, 64 % de cobertura. Falta UI y pruebas de carga. |
| Reproducibilidad (deps/build) | 1.0 | 4.0 | Lockfiles `pip-compile`, imágenes con usuario no root. Falta SBOM y digest de imagen base. |
|DX y gobierno | 1.5 | 3.5 | ruff + mypy + pre-commit + plantillas. Falta CHANGELOG, releases y responsables de CODEOWNERS. |
| Escalabilidad técnica | 1.5 | 2.5 | Caché de datos, workers, health checks. Límite de tasa en memoria (no compartido). |
| Producto / contrato | 3.0 | 3.5 | Presupuesto del usuario aún no se aplica (se avisa). Sin versionado de API. |

---

## 2. Estado verificado (medido, no supuesto)

| Comprobación | Resultado |
|---|---|
| `python -m unittest discover -s tests` | 26 tests, verde |
| `python -m pytest tests` | **No arrancaba**: `ModuleNotFoundError: test_orchestrator` (solo funcionaba con `unittest discover`) |
| Cobertura | **40 %** total; `api/routes.py` y `main.py` al **0 %** |
| `ruff check .` | **50 errores** (sin configuración de lint en el repo) |
| `ruff format --check .` | 23 de 38 ficheros sin formatear |
| `mypy` | No existía configuración ni ejecución en CI |
| Dependencias | `>=` sin fijar en los tres `requirements.txt`; **sin lockfile** |
| CI | 3 jobs (validar datos, tests, smoke). Sin lint, tipado, cobertura ni seguridad |
| Frontend | **0 %** cubierto, sin tests, ausente de CI |
| `.env` en git | Correcto: ignorado y sin secretos versionados |
| Links rotos en documentación | 1 (`docs/agent-contract-validation.md`, inexistente) |

---

## 3. Hallazgos

Severidad: **P0** bloqueante para producción · **P1** necesario para escalar · **P2** profesionalización y producto.

### P0 — Bloqueantes

| ID | Hallazgo | Impacto | Estado |
|---|---|---|---|
| P0-1 | `/api/chat` sin autenticación **ni límite de tasa**: cualquier cliente puede consumir la API key del LLM a voluntad. | Coste descontrolado + denegación de servicio | **Resuelto**: límite por ventana deslizante (`RATE_LIMIT_REQUESTS`/`RATE_LIMIT_WINDOW_SECONDS`), respuesta `429 rate_limited` |
| P0-2 | Sin observabilidad: `logger.exception` sin correlación, sin `request_id`, sin métricas. | Incidencias no diagnosticables | **Resuelto**: middleware de `X-Request-ID`, logs JSON, `GET /api/ready` y `GET /api/version` |
| P0-3 | Capa HTTP (`api/routes.py`, `main.py`) sin un solo test. El contrato público (400/422/502) no estaba automatizado. | Regresiones silenciosas en el contrato | **Resuelto**: `tests/test_api.py` (13 casos), cobertura de la capa API del 0 % al **82 %** |
| P0-4 | Dependencias sin fijar (`>=`) y sin lockfile: dos despliegues del mismo commit podían instalar versiones distintas. | Builds no reproducibles, fallos fantasma | **Resuelto**: `.in` (rangos) + lockfiles con `pip-compile`; verificado en un venv limpio con `fastapi 0.162`, `groq 1.7`, `openai 3.50` |
| P0-5 | `pytest` (el estándar de facto) no podía collects los tests. | Onboarding frustrado, cobertura invisible para quien usa pytest | **Resuelto**: `pyproject.toml` con `pythonpath` y `testpaths` |
| P0-6 | Sin puertas de calidad: lint, formato, tipado, cobertura y auditoría de dependencias ausentes del CI. | La calidad depende de la disciplina individual | **Resuelto**: CI con 7 jobs (datos, lint, mypy, tests+cobertura, smoke, `pip-audit`, build Docker) |
| P0-7 | Sin gestión de vulnerabilidades de dependencias. | CVEs sin detectar | **Resuelto**: `pip-audit` en CI + Dependabot |

### P1 — Escalabilidad y operación

| ID | Hallazgo | Impacto | Estado |
|---|---|---|---|
| P1-1 | Un único proceso Uvicorn y `docker-compose` de desarrollo (sin `restart`, sin límites de recursos, sin logs rotados). | No aguanta carga ni reinicios | **Resuelto**: workers, `restart: unless-stopped`, límites CPU/memoria, rotación de logs, healthcheck en frontend |
| P1-2 | `load_json()` leía los JSON **de disco en cada petición** (`find_demo_scenario`, `default_fee_for_currency`, presupuestos). | I/O por request; no escala | **Resuelto**: caché en memoria con invalidación por `clear_cache()` |
| P1-3 | Cliente LLM sin `timeout`, sin reintentos: una caída del proveedor colgaba la petición. | Requests colgados, coste de infraestructura | **Resuelto**: timeout por cliente, reintentos con backoff exponencial solo ante errores transitorios (429/5xx/timeout) |
| P1-4 | `history` sin límite: cualquier cliente podía inflar el prompt (coste de tokens) y el contexto. | Coste y superficie de prompt injection | **Resuelto**: `MAX_HISTORY_MESSAGES` (rechazo `400`) y recorte del historial enviado al LLM |
| P1-5 | `/api/health` devolvía `ok` siempre: no distinguía proceso vivo de servicio sano. | Sondas de orquestador dan falso positivo | **Resuelto**: `/api/health` (liveness), `/api/ready` (dependencias), `/api/version` |
| P1-6 | `FX_SOURCE=live` sin caché/TTL/circuit breaker activos por defecto. | Latencia, fragilidad y llamadas repetidas si se habilita live sin ajustes | **Parcial** - mecanismo configurable implementado en `get_fx_reference` (`FX_CACHE_TTL_SECONDS`, `FX_CIRCUIT_BREAKER_*`, por defecto off); pendiente habilitar/validar en entorno (ver §5) |
| P1-7 | El limitador de tasa es por proceso: con varias réplicas el límite real se multiplica. | Abuso no controlable en despliegue horizontal | **Pendiente** — requiere backend compartido (Redis) con la misma interfaz |
| P1-8 | Sin métricas ni trazas distribuidas; no hay forma de medir latencia, tasa de *fallback* o coste por petición. | No se puede ni operar ni justificar el coste | **Pendiente** — OpenTelemetry + exporter Prometheus |
| P1-9 | Sin SBOM, escaneo de imágenes ni digest fijado en la imagen base. | Trazabilidad de la cadena de suministro incompleta | **Pendiente** — trivy/syft en CI + digest de `python:3.11-slim` |
| P1-10 | Sin versionado de API (`/api/v1`): cualquier cambio futuro del contrato rompe clientes. | Evolución segura imposible | **Pendiente** — decidir antes de abrir a terceros (rompe el contrato actual) |
| P1-11 | Frontend: `requests` síncrono sin reintentos ni sesión reutilizable. | Errores transitorios visibles para el usuario | **Resuelto**: `Session`, reintentos con backoff solo en error de conexión, timeout alineado con el del backend |
| P1-12 | Frontend: `unsafe_allow_html` con valores de la API interpolados sin escapar (`currency`). | XSS latente si el backend devuelve datos no confiables | **Resuelto**: escapado con `html.escape` |

### P2 — Producto, contrato y gobierno

| ID | Hallazgo | Impacto | Estado |
|---|---|---|---|
| P2-1 | `context.project_budget` se acepta y **se ignora**: el usuario ve el impacto del presupuesto demo `KE-HEALTH-001`, no del suyo. Es un *default* engañoso. | Confianza del usuario; decisión de producto pendiente | **Parcial**: ahora se emite un `alert` explícito en la respuesta. **Pendiente**: aplicar el presupuesto real (feature `S1` del backlog) |
| P2-2 | `corridors.json` existía pero **no lo leía nadie**: el corredor MVP estaba hardcodeado en `routes.py` (`KE`/`KES`), contradiciendo el "agnosticismo por diseño" del README. | Mantener dos fuentes de verdad | **Resuelto**: la matriz de cobertura se lee de los datos; añadir corredor = entrada de datos |
| P2-3 | `project_budgets.json` se seleccionaba por identificador fijo (`KE-HEALTH-001`). | Misma duplicidad de fuentes | **Resuelto**: selección por país/moneda del corredor |
| P2-4 | El README contenía **dos versiones del mismo documento** en un solo fichero (líneas 1-162 y 164-448) y un enlace roto (`docs/agent-contract-validation.md`). | Ruido y confianza baja en la documentación | **Pendiente** — limpieza en curso |
| P2-5 | Documentación extensa (20+ ficheros) sin índice ni estados sincronizados con el código; el backlog marca como `[~]`/`[ ]` cosas ya terminadas. | El backlog deja de ser fuente de verdad | **Pendiente** |
| P2-6 | Sin `CHANGELOG`, sin releases, sin tags semánticos. | Trazabilidad de versiones | **Pendiente** |
| P2-7 | 11 ramas remotas obsoletas y merges de documentación sobre `main`. | Ruido en el historial | **Pendiente** |
| P2-8 | `CODEOWNERS` sin responsables reales (falta mapear los handles del equipo). | Revisiones sin dueño claro | **Pendiente** (el fichero existe; requiere los handles reales) |
| P2-9 | Accesibilidad e i18n parciales; el frontend solo en español y el mensaje al agente en inglés. | Alcance de usuarios | **Pendiente** (ya registrado como `TD-09`) |
| P2-10 | Sin persistencia ni identidad: todo es efímero por petición. | Nada de historial ni multiusuario | **Decisión de producto**, ya registrado como `TD-03` |

---

## 4. Lo que hay que preservar (activos del proyecto)

Estos elementos son la diferencia entre un MVP y una maqueta. **No deben perderse al escalar**:

1. **Determinismo donde importa**: `Decimal` en el motor de cálculo, fixtures versionados, golden case B1 verificado en CI.
2. **Honestidad en la degradación**: `deterministic_fallback` no finge tools ejecutadas (`tools_used=[]`, `is_fallback=true`, `fx_reference=null`).
3. **Parámetros financieros fuera del LLM**: el modelo nunca puede fijar importe, tasa, comisión o moneda; el backend los liga al contexto validado. Es la protección más importante del sistema.
4. **Procedencia visible**: `fx_source`, `date`, `is_mock` y `calculation_source` acompañan siempre a la cifra.
5. **Contrato congelado y documentado** en tres sitios coherentes (`docs/api-contract.md`, `shared/contracts/`, `README`).

---

## 5. Plan de escalado

### Fase 0 — Blindaje (hecha en esta iteración)

Cerrar P0 y el núcleo de P1. Resultado: el proyecto se puede desplegar en un entorno controlado y diagnosing.

- ✅ Limitador de tasa, `request_id`, logs JSON, sondas liveness/readiness/version.
- ✅ Tests de la capa HTTP, cobertura 40 % → 64 %.
- ✅ Lockfiles, ruff, mypy, pre-commit, CI con 7 jobs, Dependabot, `pip-audit`.
- ✅ Caché de datos, timeouts/reintentos del LLM, límites de historial.
- ✅ Docker: usuario no root, workers, límites, healthchecks.

### Fase 1 — Operación y resiliencia (2-4 semanas)

| Entregable | Objetivo |
|---|---|
| **Métricas + trazas** (OpenTelemetry → Prometheus/Grafana) | Latencia p50/p95, tasa de `fallback`, ratio de degraded, llamadas al LLM por petición, coste estimado |
| **Caché de FX con TTL + *circuit breaker*** (mecanismo implementado, pendiente activar/validar) | Eliminar llamadas repetidas a Frankfurter y degradar con elegancia ante caída del proveedor |
| **Rate limit compartido (Redis)** | Límite real con varias réplicas; necesario antes de escalar horizontalmente |
| **Presupuesto real del usuario** (cierra `S1` y P2-1) | Aplicar `context.project_budget` con reglas por prioridad y alertas por partida |
| **Pruebas de carga** (k6/Locust) | Objetivo de latencia y de coste por petición, y verificación del límite de tasa |
| **SBOM + escaneo de imágenes + digest fijado** | Cadena de suministro trazable |
| **`/api/v1` + política de deprecación** | Versionado del contrato antes de abrir a terceros |

### Fase 2 — Producto y plataforma (1-3 meses)

| Entregable | Objetivo |
|---|---|
| Persistencia (PostgreSQL) + identidad | Historial de simulaciones por organización y comparativa entre envíos |
| Multi-corredor real (GHS, USD→KES, etc.) desde datos | El agnosticismo deja de ser teórico |
| Cola de trabajo para simulations largas | Trabajo asíncrono + notificación de resultado |
| Internacionalización y accesibilidad | Más allá del español/inglés |
| Panel de observación para equipos ONG | Comparativa de escenarios históricos y auditoría de supuestos |

### Fase 3 — Industrialización (3-6 meses)

- Proveedor de FX con acuerdo comercial y SLA (no Frankfurte de uso hobby).
- Motor de escenarios configurable (bandas de variación, múltiples corredores, escenarios Monte Carlo).
- API pública versionada con claves de cliente y cuotas por organización.
- Contribución abierta: `CONTRIBUTING.md`, plantillas de issue y publicación de releases.

---

## 6. Definición de "hecho" (calidad mínima exigible)

Un cambio se considera terminado cuando:

- [ ] `pytest tests -q` en verde y cobertura global ≥ 60 % (sin bajar).
- [ ] `ruff check .` y `ruff format --check .` en verde.
- [ ] `mypy backend` en verde.
- [ ] `node scripts/validate-data.mjs` en verde si se han tocado datos.
- [ ] `pip-audit` sin vulnerabilidades conocidas en las dependencias tocadas.
- [ ] Si cambia el contrato: `docs/api-contract.md`, `shared/contracts/contracts.md` y las pruebas de contrato actualizados en el **mismo** PR.
- [ ] Sin secretos ni datos personales en código, logs o fixtures.
- [ ] Toda respuesta degradada declara su modo (`execution_mode`, `degraded`, `alerts`).

---

## 7. Riesgos de esta transformación

| Riesgo | Mitigación |
|---|---|
| Romper el contrato congelado | Los cambios son **aditivos**: `429 rate_limited`, `GET /api/ready`, `GET /api/version`, cabecera `X-Request-ID`. El contrato existente (`200/400/422/502`) se mantiene intacto y verificado por tests |
| El *fallback* determinista deja de coincidir con los fixtures | El golden case B1 sigue verificado en CI (tests + smoke) tras cada cambio |
| Subir a `fastapi 0.162` / `groq 1.7` / `openai 3.50` rompe algo no cubierto | Los locks se validaron en un venv limpio con la suite completa en verde; conviene una prueba manual con un LLM real antes de publicar |
| El limitador en memoria no sirve con varias réplicas | Documentado como limitación (P1-7); el diseño de `RateLimiter` permite sustituir el backend sin tocar la API |
| Sobrecarga de trabajo para un equipo de 4 personas | El plan está priorizado por fases; Fase 0 ya está hecha y las fases 1-3 son independientes entre sí |

---

## 8. Anexo: comandos de trabajo

```bash
# Instalación reproducible
pip install -r backend/requirements.txt -r dev-requirements.txt   # backend + calidad
pip install -r requirements.txt                                    # frontend

# Regenerar lockfiles (tras tocar los .in)
pip install pip-tools
pip-compile --strip-extras -o backend/requirements.txt backend/requirements.in
pip-compile --strip-extras -o requirements.txt requirements.in
pip-compile --strip-extras -o dev-requirements.txt dev-requirements.in

# Calidad (lo que ejecuta CI)
pytest tests -q
ruff check . && ruff format --check .
mypy backend
coverage run --source=backend,frontend -m pytest tests -q && coverage report

# Git hooks locales
pre-commit install
```
