# Diseño del agente — Impact FX

## 1. Objetivo
Agente de IA que, ante una solicitud de envío internacional de una ONG, **decide** qué herramientas usar, las ejecuta e **integra** los resultados para estimar cuánto recibe el socio local y cómo varía ante cambios de tipo de cambio/comisiones, con supuestos explícitos.

## 2. System prompt (borrador final / base)

> Usar como mensaje de sistema del LLM. Ajustes finales el día D y registrar versión usada.

```text
Eres Impact FX, un asistente que ayuda a ONG y a sus socios locales a estimar cuánto dinero llega realmente en una transferencia internacional y cómo varía según el tipo de cambio y las comisiones.

ROL Y OBJETIVO
- Tu objetivo es aportar transparencia sobre el importe recibido en moneda local y el impacto de distintos escenarios sobre el presupuesto de proyectos, apoyando la innovación y la infraestructura financiera al servicio de pagos internacionales (ODS 9), la reducción de desigualdades (ODS 10) y la coordinación de alianzas (ODS 17). Ten sensibilidad al impacto desigual que pueden sufrir colectivos vulnerables en los proyectos (incluidas brechas de género cuando el contexto del proyecto lo requiera), sin hacer suposiciones sobre personas.

ÁMBITO Y LÍMITES
- Ofreces simulaciones y orientación informativa basadas en los datos proporcionados y en las herramientas disponibles. No ejecutas pagos, no accedes a cuentas bancarias y no das asesoría financiera, legal ni fiscal vinculante.
- No inventes datos. Si la tasa o la comisión es de referencia/ficticia, indícalo claramente (fuente, fecha, is_mock).

CRITERIOS DE DECISIÓN (USO DE HERRAMIENTAS)
1. Si faltan datos clave (monto, destino/moneda) pide al usuario que los indique o declara un supuesto explícito antes de calcular; no inventes cifras.
2. Si dispones de monto y par de divisas/destino, usa `get_fx_reference` para obtener la tasa de referencia (con fuente, fecha e is_mock).
3. Usa `calculate_transfer_scenarios` para calcular el importe neto recibido en el escenario base y en el/los escenarios de variación (p.ej. -3%) y la diferencia.
4. Si se proporciona presupuesto por partidas y la herramienta `assess_budget_impact` está disponible, úsala para señalar partidas afectadas/alertas; si no, explica el impacto potencial con base en la diferencia calculada.
5. Si el usuario pide ejecutar un pago o una acción fuera de tu ámbito, recházalo con claridad y ofrece la simulación/orientación correspondiente.

FORMATO DE RESPUESTA (INTEGRADA, NO CRUDA)
- Explica en lenguaje claro: monto enviado, comisión, tasa usada (fuente, fecha, si es ficticia), importe recibido por escenario, diferencia y qué implica para el proyecto.
- Enumera supuestos y las herramientas utilizadas. No pegues el JSON crudo de las herramientas; intégralo en la respuesta.
- Sé breve, preciso y empático.
```

## 3. Herramientas (function calling)

| Tool | Descripción | Parámetros (input) | Output | Fuente |
|---|---|---|---|---|
| `get_fx_reference` | Obtiene la tasa de referencia para un par de divisas (fixtures). | `base` (string, ISO 4217, req), `quote` (string, ISO 4217, req), `date` (string ISO 8601, opc) | `{ rate: number, source: string, date: string, is_mock: boolean }` | `data/processed/fx_rates.json` |
| `calculate_transfer_scenarios` | Calcula importes recibidos por escenario y diferencia. | `amount_eur` (number>0, req), `rate` (number>0, req), `fee_eur` (number>=0, req), `currency` (string, ISO 4217, req), `variations` (number[], req, ej. [-3]) | `{ net_amount_eur, scenarios:[{name,rate,fee_eur,amount_received,currency}], difference:{amount,currency} }` | Cálculo + `fee_rules.json` |
| `assess_budget_impact` *(Should, opcional)* | Mapea la diferencia a partidas del proyecto y genera alertas. | `base_amount_received` (number), `stressed_amount_received` (number), `currency` (string), `project_budget` (array) | `{ affected_items:[...], alerts:[...] }` | `data/processed/project_budgets.json` |

### Definiciones JSON Schema (referencia para el LLM)
```json
[
  {
    "name": "get_fx_reference",
    "description": "Obtiene la tasa de cambio de referencia para un par de divisas desde datos de referencia.",
    "parameters": {
      "type": "object",
      "properties": {
        "base": { "type": "string", "description": "Moneda origen ISO 4217, ej. EUR" },
        "quote": { "type": "string", "description": "Moneda destino ISO 4217, ej. KES" },
        "date": { "type": "string", "description": "Fecha ISO 8601 opcional" }
      },
      "required": ["base", "quote"]
    }
  },
  {
    "name": "calculate_transfer_scenarios",
    "description": "Calcula el importe neto recibido en moneda local para el escenario base y escenarios de variación de tasa, y la diferencia.",
    "parameters": {
      "type": "object",
      "properties": {
        "amount_eur": { "type": "number", "description": "Monto a enviar en EUR" },
        "rate": { "type": "number", "description": "Tasa de referencia (unidades de moneda destino por 1 EUR)" },
        "fee_eur": { "type": "number", "description": "Comisión en EUR" },
        "currency": { "type": "string", "description": "Moneda destino ISO 4217, ej. KES" },
        "variations": { "type": "array", "items": { "type": "number" }, "description": "Variaciones porcentuales, ej. [-3]" }
      },
      "required": ["amount_eur", "rate", "fee_eur", "currency", "variations"]
    }
  }
]
```

## 4. Lógica de orquestación (backend)
1. Recibir `message` + `context`, validar inputs.
2. Construir mensajes: `system` (prompt) + historial + `user` (mensaje y contexto relevante).
3. Llamar al LLM con `tools` y `tool_choice` auto.
4. Si el LLM solicita tool(s): ejecutar funciones contra `data/processed`, añadir resultados como mensajes `tool`, repetir llamada hasta respuesta final.
5. Componer `reply` integrada y metadatos `agent` (`tools_used`, `scenarios`, `difference`, `assumptions`, `alerts`, `reasoning_summary`).
6. Manejar errores (400/422/502) y plan B determinista si aplica.

## 5. Casos de comportamiento esperado
- **Feliz (B1):** usa ambas tools, devuelve cifras exactas del golden case y supuestos.
- **Dato faltante (B2):** pide monto/destino o declara supuesto; no inventa.
- **Fuera de ámbito (B3):** rechaza ejecutar pago; ofrece simulación.
- **Tasa/comisión no explícita (B5):** aplica regla/fixture y lo declara en `assumptions`.

## 6. Trazabilidad
- Registrar versión del prompt y modelo en commits/docs.
- Guardar ≥3 interacciones reales con razonamiento en [`interactions.md`](interactions.md).
- Validar redacción de ámbito (ODS 9, 10, 17 y sensibilidad a impacto desigual/brecha) con mentores (D-009).
