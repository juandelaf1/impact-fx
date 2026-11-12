# Deuda técnica — Impact FX

Registro de deuda **consciente** aceptada para cumplir el MVP, con mitigaciones y plan de pago.

| ID | Ítem | Motivo (por qué se acepta) | Impacto/Riesgo | Mitigación actual | Prioridad de pago | Propuesta futura |
|---|---|---|---|---|---|---|
| TD-01 | Tasas y comisiones de referencia/demo (fixtures y/o proveedor referencia) | Determinismo y trazabilidad en MVP | No equivale a cotización ejecutable/mercado real | `fx_reference` (`rate,source,date,is_mock`), `fx_source`, supuestos explícitos; Frankfurter como referencia externa | Media | Integrar cotización ejecutable/proveedor real con fallback y trazabilidad |
| TD-02 | Cobertura limitada de corredores/monedas (MVP KE/KES, EUR→KES) | Tiempo y foco de demo | Poca generalización | Diseño y datos agnósticos por corredor/fixtures adicionales (B1b/B1c) | Media | Ampliar `corridors/rates/fees`, validaciones y UI |
| TD-03 | Sin persistencia/BD ni autenticación | Fuera del MVP | Sin historial multi-sesión ni usuarios | Estado efímero/contexto por petición | Baja | Almacenamiento, identidad y auditoría si evoluciona |
| TD-04 | Cobertura E2E automatizada (UI/Docker/LLM real) parcial | Tiempo/entorno | Riesgo de regresión en integración visual y despliegue | 38 tests unitarios/lógica, validación de datos, smoke script, CI (validate/tests/smoke), verificación API real de B1–B3/fallback | Media | Tests de integración HTTP/UI, contract tests FE↔BE, E2E en contenedor, pruebas con proveedor LLM estable/mockeado |
| TD-05 | Observabilidad y manejo operativo avanzados | Tiempo | Diagnóstico limitado en producción | Errores 400/422/502 estandarizados y sanitizados, metadatos de ejecución, fallback determinista con alertas | Media | Logging estructurado, trazas de tools/LLM, métricas y monitoreo de degradación/fallback |
| TD-06 | Seguridad a nivel MVP | Alcance hackathon | Superficie no endurecida | Validación/sanitización, CORS restringido, claves en `.env` (no commiteado), sin ejecución de pagos | Alta (si evoluciona) | Hardening, límites de tasa, secretos seguros, revisión de seguridad |
| TD-07 | Acoplamiento al formato/proveedor LLM y parsing de tool-calling | Velocidad de integración | Cambio de proveedor/modelo puede requerir ajustes | Cliente/config aislados y contrato de tools propio; fallback determinista | Media | Abstracción de proveedor, adaptadores y pruebas de compatibilidad |
| TD-08 | Impacto presupuestario simplificado (demo sintético, agregado) | Priorizar Must y trazabilidad | No refleja partidas reales ni asigna déficit específico | `budget_impact` determinista marcado como demo/sintético, sin atribución a partidas; tool `assess_budget_impact` opcional | Baja | Modelo de partidas/prioridades con datos reales y reglas validadas |
| TD-09 | i18n/accesibilidad/UX parcial | Priorizar funcionalidad | Alcance limitado | UI clara, mensajes de error/estados y metadatos visibles | Baja | Accesibilidad, idiomas y refinamiento UX |

## Criterios de gestión
- **Registrar:** cualquier atajo nuevo se añade aquí (ID, motivo, mitigación).
- **No aceptar:** exposición de secretos, datos personales reales, ni inventar resultados (trazabilidad/supuestos obligatorios).
- **Cierre reto:** priorizar evidencia E2E (TD-04), consistencia contrato/frontend-documentación y revisión de seguridad/config (TD-06) antes de demo final.