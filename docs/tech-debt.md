# Deuda técnica — Impact FX

Registro de deuda **consciente** aceptada para cumplir el MVP en 4–5 h, con mitigaciones y plan de pago.

| ID | Ítem | Motivo (por qué se acepta) | Impacto/Riesgo | Mitigación actual | Prioridad de pago | Propuesta futura |
|---|---|---|---|---|---|---|
| TD-01 | Tasas y comisiones estáticas (fixtures mock) | Determinismo, sin dependencia externa, cifras verificables | No refleja mercado real | `is_mock`, `source`, `date` y supuestos explícitos en respuesta | Media | Adaptador `get_fx_reference` a API real (p.ej. proveedor FX) con fallback a fixture |
| TD-02 | Cobertura limitada de corredores (demo 1–2) | Tiempo y simplicidad | Poca generalización visible | Diseño y esquemas agnósticos; 2º corredor en datos | Media | Ampliar `corridors/rates/fees` y UI de selección |
| TD-03 | Sin persistencia/BD ni autenticación | Fuera del MVP | Sin historial multi-sesión ni usuarios | Estado efímero/contexto por petición | Baja | Añadir almacenamiento e identidad si el producto evoluciona |
| TD-04 | Tests automatizados mínimos | Tiempo | Riesgo de regresiones | `demo_scenarios.json` (golden), script de validación de datos y benchmark manual B1–B6 | Alta | Unit tests de tools/cálculos e integración de `/api/chat` |
| TD-05 | Manejo de errores y observabilidad básicos | Tiempo | Diagnóstico limitado en fallos | Errores estandarizados (400/422/502), mensajes claros, fallback determinista | Media | Logging estructurado, trazas de tools, métricas |
| TD-06 | Seguridad a nivel MVP (validación básica) | Alcance hackathon | Superficie de ataque no endurecida | Validación/sanitización de inputs, claves en `.env`, CORS restringido | Alta (si evoluciona) | Hardening, límites de tasa, revisión de seguridad |
| TD-07 | Acoplamiento al formato del proveedor LLM | Velocidad de integración | Cambio de proveedor costoso | Cliente LLM aislado en `config/` y contrato de tools propio | Media | Capa de abstracción de proveedor/modelo |
| TD-08 | `assess_budget_impact` y análisis de partidas simplificado/ausente | Priorizar Must | Impacto por partida menos granular | Diferencia global explicada; tool como Should | Baja | Implementar tool completa y reglas por prioridad de partida |
| TD-09 | i18n/accesibilidad/UX parcial | Priorizar funcionalidad | Alcance de usuarios limitado | UI clara y legible en flujo principal | Baja | Mejoras de accesibilidad, idiomas y diseño |

## Criterios de gestión
- **Registrar:** cualquier atajo nuevo tomado el día D se añade aquí (ID, motivo, mitigación).
- **No aceptar:** exposición de secretos, datos personales reales, ni inventar resultados (la trazabilidad/supuestos son obligatorios).
- **Revisión:** al cierre del reto, priorizar TD-04, TD-06 y TD-01 para una siguiente iteración.
