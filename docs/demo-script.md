# Guion de demo — Impact FX (8–10 minutos)

## Estructura y tiempos
| Bloque | Tiempo | Contenido | Responsable sugerido |
|---|---:|---|---|
| 1. Problema y ODS | 1:30 | Contexto: ONG envía fondos y no sabe cuánto llega; impacto en partidas. ODS 9, 10 y 17, valor para coordinación con socio local y sensibilidad al impacto desigual | José / equipo |
| 2. Solución y diseño del agente | 2:00 | Qué hace Impact FX. Arquitectura (FE/BE REST). **System prompt** (rol, ámbito, límites), **2 tools** y criterios de decisión (petición → decisión → tools → respuesta integrada) | Gema / Juan |
| 3. Demo en vivo (núcleo) | 3:00 | Caso Kenia en la app: mostrar petición, ejecución de tools (`tools_used`), escenarios, diferencia, supuestos/fuente y respuesta integrada en UI | Laura (UI) + José (narración) |
| 4. Técnico y retos | 1:30 | Stack, endpoints, datos deterministas/agnósticos, decisiones clave, desafíos y cómo se resolvieron | Juan / Gema |
| 5. Aprendizajes y cierre | 1:00 | Aprendizajes en 4–7 h, próximos pasos (tasas reales, más corredores) | Equipo |
| 6. Preguntas | 2:00 | Q&A | Todos |

## Guion detallado

### Preparación técnica — Docker Compose
Desde la raíz, validar y arrancar el entorno reproducible:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
curl -fsS http://localhost:3001/api/health
```

Confirmar que frontend y backend están `healthy` antes de abrir `http://localhost:8501`. Si esos puertos ya están ocupados, usar `BACKEND_HOST_PORT=3002 FRONTEND_HOST_PORT=8502` al ejecutar Compose y abrir `http://localhost:8502`.

### 1) Problema y ODS (1:30)
- "Cuando una ONG envía fondos al extranjero, presupuestar en euros no garantiza cuánto recibirá el socio local: el tipo de cambio y las comisiones pueden reducir el importe y dejar partidas críticas sin cobertura."
- "Impact FX busca reducir esa desigualdad de información (ODS 10) y mejorar la coordinación entre aliados (ODS 17), aportando simulaciones transparentes con supuestos explícitos."

### 2) Solución y diseño del agente (2:00)
- Mostrar flujo: usuario → `POST /api/chat` → agente (LLM + system prompt) **decide** → `get_fx_reference` y `calculate_transfer_scenarios` → **integra** resultados.
- Mencionar: 2 herramientas con parámetros definidos (function calling), respuesta integrada (no cruda), tasa de referencia ficticia identificada (`source`, `date`, `is_mock`), límites (no ejecuta pagos).

### 3) Demo en vivo (3:00) — caso B1
- **Entrada:** 10.000 EUR, destino Kenia (KES), comisión 40 EUR, variación −3%.
- **Narrar en vivo:** "El agente identifica los datos, obtiene la tasa de referencia y calcula los escenarios".
- **Mostrar en pantalla:** `tools_used` = `get_fx_reference`, `calculate_transfer_scenarios`; base **1.444.200 KES**; estrés −3% **1.400.874 KES**; diferencia **43.326 KES**; supuestos (tasa 145, demo_reference, 2026-11-12, `is_mock=true`, comisión 40 EUR) y explicación integrada.
- **Mensaje clave:** el resultado es verificable, trazable y comprensible para la toma de decisiones.
- La ejecución normal de B1 desde la UI se probó localmente el 2026-11-12. En esa prueba se vieron las cifras, la referencia ficticia y las dos herramientas en el panel estructurado. La visualización fue local, no Docker.
- En la prueba Docker Compose del 2026-11-12, la UI mostró correctamente la tasa, fecha, fuente, condición ficticia e impacto. Sin embargo, una llamada solo reportó `get_fx_reference`; otra llamada del smoke test sí reportó ambas tools. No afirmar que las dos tools se ejecutan de forma reproducible hasta corregir/verificar el comportamiento.
- El backend todavía no devuelve `agent.fx_reference` ni `agent.is_fallback`; por ahora, la tasa, fecha y procedencia se ven dentro del texto/supuestos y el modo se infiere del resumen o del aviso de demo. No presentar esos datos como campos estructurados existentes.
- La UI muestra una explicación general del impacto; no presenta actualmente una evaluación por partida de un presupuesto recibido.

### 4) Técnico y retos (1:30)
- Stack elegido, endpoint `/api/chat`, datos en `data/processed` (agnóstico por diseño, demo acotada), validación y `.env` para claves.
- Reto típico: integrar tool calling y asegurar respuesta integrada; mitigación: contratos/datos congelados y golden case.

### 5) Cierre (1:00)
- Aprendizajes: priorizar ciclo completo y determinismo; trabajo por roles y contratos.
- Evolución: adaptador de tasas reales, más corredores, impacto por partidas.

## Plan B (si algo falla en vivo)
| Falla | Acción inmediata |
|---|---|
| Fuente FX live no disponible | `get_fx_reference` intenta usar la tasa local; identificarla como ficticia y diferenciar la fuente configurada (`FX_SOURCE`) de la fuente efectiva (`fx_reference.source`). Esta ruta está cubierta por pruebas de tool, no por una prueba E2E en la UI. |
| LLM lento/cae o sin red | Usar el fallback determinista desde `demo_scenarios.json` solo si hay coincidencia. El modo debe quedar explícito; no afirmar que se ejecutaron tools si solo se leyó el fixture. |
| API/backend caído | La UI puede mostrar su **demo local** con el aviso “Demo preview”. Es una vista de frontend y no equivale al fallback del agente. |
| Error puntual en UI | Repetir petición o mostrar caso precargado y explicar el flujo con `docs/interactions.md` |
| Tiempo ajustado | Recortar bloque 4 y priorizar bloque 3 (demo del ciclo completo) |

## Checklist previo a presentar
- [ ] URL (o entorno local) abierto y probado con B1.
- [ ] `.env` correcto, sin exponer claves en pantalla.
- [ ] Números del caso Kenia memorizados/verificados (1.444.200 / 1.400.874 / Δ 43.326 KES).
- [ ] `tools_used` y supuestos visibles en la UI o mencionables.
- [x] Docker Compose configurado, imágenes construidas, ambos health checks y conexión FE→BE verificados.
- [ ] Repetir B1 en Docker hasta que la selección de ambas tools sea consistente y se devuelvan los metadatos estructurados.
- [ ] Acordar con backend/frontend los campos de modo y referencia FX, y el alcance del impacto presupuestario antes de presentarlos como funcionalidad.
- [x] Probar el fallback determinista y la demo local; describir sus limitaciones sin confundir los modos.
