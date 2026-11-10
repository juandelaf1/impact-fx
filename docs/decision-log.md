# Decision Log — Impact FX

Registro de decisiones clave del proyecto. Objetivo: evitar rediscutir, alinear al equipo y justificar elecciones técnicas/funcionales.

> Formato: **[ID] Fecha · Estado · Decisión · Contexto · Alternativas · Consecuencias · Responsable**

## Registro

| ID | Fecha | Estado | Decisión | Contexto / Motivo | Alternativas consideradas | Consecuencias / Seguimiento | Responsable |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-11-__ | Propuesta | **Producto: Impact FX** (simulador de impacto de transferencia para ONG, EUR→KES demo) | Encaje alto con Ebury (pagos/divisas) y ODS 10,17; demo visual y verificable | PayGuard AI, FinBridge, Open Doors AI, Global Start | Foco en transparencia de importe recibido y escenarios | Equipo G1 |
| D-002 | 2026-11-__ | Propuesta | **Alcance MVP:** 1 corredor (Kenia), 2 escenarios (base, −3%), 2 tools, 1 pantalla, 1 endpoint principal; agnóstico por diseño pero demo acotada | 4–5 h de construcción efectiva; priorizar ciclo completo funcional | Multi-país en vivo, más tools/UI | Añadir corredores/impacto por partidas solo si Must estable (Should) | Equipo G1 |
| D-003 | 2026-11-__ | Pendiente | **Stack:** Backend ______, Frontend ______ | Elegir lo que el equipo domine para minimizar fricción | Node.js+Express / React+Vite; Python+FastAPI / HTML-JS | Cerrar antes de preparación; documentar en README/arquitectura | Juan, Laura |
| D-004 | 2026-11-__ | Pendiente | **LLM principal + fallback:** ______ (modelo con *function calling*) | Necesario agente con tools; fiabilidad en demo | Groq (API compatible OpenAI), OpenAI, Gemini | Probar smoke test con tools; guardar fallback determinista (`demo_scenarios.json`) | Juan, Gema |
| D-005 | 2026-11-__ | Aprobada | **Datos deterministas (fixtures) como fuente de verdad en demo**, tasas ficticias identificadas (`is_mock/source/date`) | Evitar dependencia de internet/APIs/scraping; garantizar cifras verificables | API FX en vivo, scraping | Números reproducibles (B1); posible adaptador API futuro (deuda técnica) | José Melo |
| D-006 | 2026-11-__ | Aprobada | **No scraping** de webs; API de tasas solo opcional con fallback a fixture | Scraping frágil/riesgoso en hackathon; comisiones sin API universal fiable | Scraping, integración bancaria real | Menor riesgo; supuestos documentados | Equipo G1 |
| D-007 | 2026-11-__ | Aprobada | **Contratos API/tools y esquemas de datos congelados** antes del día D | Permitir trabajo en paralelo sin romper integración | Cambios ad-hoc | Cambios solo con aviso y commit conjunto | Equipo G1 |
| D-008 | 2026-11-__ | Aprobada | **2 tools Must:** `get_fx_reference`, `calculate_transfer_scenarios` (agnósticas por parámetros) | Cumple ciclo petición→decisión→tools→respuesta integrada con mínimo robusto | 1 tool, 3+ tools | `assess_budget_impact` pasa a Should | Gema, Juan |
| D-009 | 2026-11-__ | Aprobada | **System prompt**: rol ONG, ámbito ODS 10,17 con sensibilidad al impacto desigual (incluida brecha de género según contexto del proyecto), límites (no pagos/asesoría vinculante), criterios de decisión y supuestos explícitos | Requisito 4.1 del briefing y encaje ODS; transparencia | Ámbito genérico sin matiz | **Validar redacción con mentores/organización** | Gema |
| D-010 | 2026-11-__ | Aprobada | **Plan B:** demo local y/o respuesta determinista desde `demo_scenarios.json` si falla LLM/red/deploy | Proteger demo en vivo | Depender solo de entorno en vivo | Priorizar demo funcional sobre despliegue perfecto | Equipo G1 |
| D-011 | 2026-11-__ | Aprobada | **Definition of Done MVP:** ciclo completo, ≥2 tools, cifras Kenia correctas, respuesta integrada, B1–B3, ≥3 interacciones, docs y URL/plan B, sin claves en repo | Cubre requisitos esenciales/técnicos/entregables | DoD laxo | Go/no-go claro en día D | José Melo (coord.) |

## Cómo usar este log
- **Añadir decisión:** nueva fila con ID incremental, fecha, estado (`Propuesta`/`Pendiente`/`Aprobada`/`Rechazada`/`Superseded`), contexto, alternativas y responsable.
- **Cambiar una decisión:** marcar la anterior como `Superseded` y referenciar el nuevo ID.
- **Momento clave:** cerrar D-003, D-004 y la validación de D-009 **antes del jueves**.
