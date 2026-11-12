# Deuda técnica — Impact FX

Registro de deuda **consciente** aceptada para cumplir el MVP en 4–5 h, con mitigaciones y plan de pago.

| ID | Ítem | Motivo (por qué se acepta) | Impacto/Riesgo | Mitigación actual | Prioridad de pago | Propuesta futura |
|---|---|---|---|---|---|---|
| TD-01 | Tasas y comisiones estáticas (fixtures mock) | Determinismo, sin dependencia externa, cifras verificables | No refleja mercado real | `is_mock`, `source`, `date` y supuestos explícitos en respuesta | Media | Adaptador `get_fx_reference` a API real (p.ej. proveedor FX) con fallback a fixture |
| TD-02 | Cobertura limitada de corredores (demo 1–2) | Tiempo y simplicidad | Poca generalización visible | Diseño y esquemas agnósticos; 2º corredor en datos | Media | Ampliar `corridors/rates/fees` y UI de selección |
| TD-03 | Sin persistencia/BD ni autenticación | Fuera del MVP | Sin historial multi-sesión ni usuarios | Estado efímero/contexto por petición | Baja | Añadir almacenamiento e identidad si el producto evoluciona |
| TD-04 | Cobertura de tests automatizados aún parcial | Tiempo | Riesgo de regresiones en integración/contrato | Golden cases en datos, validación de datos, unit tests de tools/orquestador, smoke backend y CI (`validate`, `backend-tests`, `backend-smoke`) | Media | Añadir tests de integración de `/api/chat` (400/422/502) y contract tests FE↔BE |
| TD-05 | Manejo de errores y observabilidad básicos (parcialmente mitigado) | Tiempo | Diagnóstico limitado en fallos en producción/demo | Errores estandarizados (400/422/502), validación de datos mínimos, fallback determinista con motivo/alertas | Media | Logging estructurado, trazas de tools/LLM, métricas y monitoreo de fallback/failover |
| TD-06 | Seguridad a nivel MVP (validación básica) | Alcance hackathon | Superficie de ataque no endurecida | Validación/sanitización de inputs, claves en `.env`, CORS restringido | Alta (si evoluciona) | Hardening, límites de tasa, revisión de seguridad |
| TD-07 | Acoplamiento al formato del proveedor LLM | Velocidad de integración | Cambio de proveedor costoso | Cliente LLM aislado en `config/` y contrato de tools propio | Media | Capa de abstracción de proveedor/modelo |
| TD-08 | `assess_budget_impact` y análisis de partidas simplificado/ausente | Priorizar Must | Impacto por partida menos granular | Diferencia global explicada; tool como Should | Baja | Implementar tool completa y reglas por prioridad de partida |
| TD-09 | i18n/accesibilidad/UX parcial | Priorizar funcionalidad | Alcance de usuarios limitado | UI clara y legible en flujo principal | Baja | Mejoras de accesibilidad, idiomas y diseño |

## Criterios de gestión
- **Registrar:** cualquier atajo nuevo tomado el día D se añade aquí (ID, motivo, mitigación).
- **No aceptar:** exposición de secretos, datos personales reales, ni inventar resultados (la trazabilidad/supuestos son obligatorios).
- **Revisión:** al cierre del reto, priorizar TD-04, TD-06 y TD-01 para una siguiente iteración.
