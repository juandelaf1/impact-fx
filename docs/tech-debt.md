# Deuda técnica — Impact FX

Registro de deuda **consciente** aceptada para cumplir el MVP en 4–5 h, con mitigaciones y plan de pago.

> **Actualización 2026-11-13 (profesionalización / Fase 0 de la auditoría):** TD-04, TD-05 y TD-06 se han mitigado en parte (tests de API, cobertura 40 %→64 %, lint/tipado/cobertura/seguridad en CI, logs estructurados con `request_id`, rate limiting). Los riesgos que siguen abiertos están en TD-10 a TD-13. Ver [`audit-escalado.md`](audit-escalado.md).

| ID | Ítem | Motivo (por qué se acepta) | Impacto/Riesgo | Mitigación actual | Prioridad de pago | Propuesta futura |
|---|---|---|---|---|---|---|
| TD-01 | Tasas y comisiones estáticas (fixtures mock) | Determinismo, sin dependencia externa, cifras verificables | No refleja mercado real | `is_mock`, `source`, `date` y supuestos explícitos en respuesta | Media | Adaptador `get_fx_reference` a API real (p.ej. proveedor FX) con fallback a fixture |
| TD-02 | Cobertura limitada de corredores (demo 1–2) | Tiempo y simplicidad | Poca generalización visible | Matriz de cobertura en datos (`corridors.json`) y leída por el backend: añadir corredor es una entrada de datos | Media | Ampliar `corridors/rates/fees` y UI de selección |
| TD-03 | Sin persistencia/BD ni autenticación | Fuera del MVP | Sin historial multi-sesión ni usuarios | Estado efímero/contexto por petición; límite de tasa por IP | Baja | Añadir almacenamiento e identidad si el producto evoluciona |
| TD-04 | Cobertura de tests automatizados aún parcial | Tiempo | Riesgo de regresiones en integración/contrato | **Actualizado:** 46 tests (unitarios, API HTTP y servicios frontend), cobertura global 64 %, matriz 400/422/429/502 y golden case B1 en CI; falta cobertura de la UI Streamlit | Media | Tests de UI con `streamlit.testing.v1.AppTest` y pruebas de carga |
| TD-05 | Manejo de errores y observabilidad básicos | Tiempo | Diagnóstico limitado en fallos en producción/demo | **Actualizado:** errores estandarizados (400/422/429/502), logging estructurado JSON con `request_id`, `GET /api/ready`, `GET /api/version`; falta métricas y trazas | Media | OpenTelemetry + Prometheus/Grafana y alertas sobre tasa de `fallback` |
| TD-06 | Seguridad a nivel MVP (validación básica) | Alcance hackathon | Superficie de ataque no endurecida | **Actualizado:** validación de inputs, límites de tasa, claves en `.env`, CORS restringido, `pip-audit` y Dependabot en CI; falta autenticación de clientes | Alta (si evoluciona) | API keys por organización, cuotas, TLS, revisión de seguridad externa |
| TD-07 | Acoplamiento al formato del proveedor LLM | Velocidad de integración | Cambio de proveedor costoso | Cliente LLM aislado en `config/` y contrato de tools propio | Media | Capa de abstracción de proveedor/modelo |
| TD-08 | `assess_budget_impact` y análisis de partidas simplificado/ausente | Priorizar Must | Impacto por partida menos granular | Diferencia global explicada; tool como Should. El MVP **avisa** en `alerts` cuando el usuario envía presupuesto que no se aplica | Baja | Implementar tool completa y reglas por prioridad de partida |
| TD-09 | i18n/accesibilidad/UX parcial | Priorizar funcionalidad | Alcance de usuarios limitado | UI clara y legible en flujo principal; escapado de HTML en valores de la API | Baja | Mejoras de accesibilidad, idiomas y diseño |
| TD-10 | Límite de tasa en memoria (por proceso) | Simplicidad | Con varias réplicas, el límite real se multiplica | Interfaz `RateLimiter` desacoplada del backend | Media | Sustituir por contador compartido (Redis) sin tocar la API |
| TD-11 | Caché de FX en modo `live` limitada (mecanismo opcional) | Tiempo/compatibilidad | Sin caché/circuit breaker activos por defecto, puede haber llamadas repetidas y menor resiliencia ante caídas | Mecanismo configurable implementado (`FX_CACHE_TTL_SECONDS`, `FX_CIRCUIT_BREAKER_*`, por defecto off), fallback local a fixtures y `is_mock` | Media | Habilitar/ajustar TTL y circuit breaker en entorno `live`, validar latencia y comportamiento ante fallos |
| TD-12 | Sin métricas ni trazas distribuidas | Tiempo | No se puede medir latencia, coste ni degradación | Logs JSON por petición con duración | Media | OpenTelemetry, exporter Prometheus, panel de operación |
| TD-13 | API sin versionado (`/api/v1`) | MVP | Cualquier cambio futuro rompe clientes | Contrato congelado y documentado + tests de contrato | Media | Versionar y definir política de deprecación antes de abrir a terceros |
| TD-14 | Dependencias de runtime fijadas, sin SBOM ni digest de imagen | Tiempo | Trazabilidad incompleta de la cadena de suministro | Lockfiles `pip-compile` reproducibles + `pip-audit` en CI | Baja | SBOM (syft), escaneo de imágenes (trivy) y digest fijado de la imagen base |

## Criterios de gestión
- **Registrar:** cualquier atajo nuevo tomado el día D se añade aquí (ID, motivo, mitigación).
- **No aceptar:** exposición de secretos, datos personales reales, ni inventar resultados (la trazabilidad/supuestos son obligatorios).
- **Revisión:** al cierre del reto, priorizar TD-04, TD-06 y TD-01 para una siguiente iteración.
