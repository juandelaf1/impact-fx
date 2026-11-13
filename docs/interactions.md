# Interacciones de ejemplo (con razonamiento del agente)

> Requisito del briefing: **≥3 ejemplos de interacción con el razonamiento del agente**.  
> Los ejemplos I1–I3 son de referencia (alineados al golden case y comportamiento esperado). El día D, **sustituir o complementar** con capturas/resultados de ejecuciones reales y anotar modelo/prompt usado.

---

## I1 — Caso feliz: simulación EUR→KES con 2 escenarios (B1)
**Petición (usuario):**
> "Quiero enviar 10.000 EUR a Kenia para un proyecto de salud. La comisión es 40 EUR. ¿Cuánto recibiría el socio local si la tasa cae un 3%?"

**Contexto enviado:** `amount_eur=10000`, `destination_country=KE`, `currency=KES`, `fee_eur=40`, `scenario_drop_pct=3`.

**Razonamiento / decisión del agente:**
1. Identifica datos completos (monto, destino KES, comisión, variación). No necesita pedir aclaraciones.
2. Decide obtener tasa de referencia → llama `get_fx_reference(base="EUR", quote="KES")`.
3. Con la tasa, decide calcular escenarios → llama `calculate_transfer_scenarios(amount_eur=10000, rate=145.0, fee_eur=40, variations=[-3])`.
4. Integra resultados en lenguaje claro, declarando supuestos (tasa ficticia, fuente, fecha) y explicando la diferencia.

**Herramientas usadas:**
- `get_fx_reference` → `{ "rate":145.0, "source":"demo_reference", "date":"2026-11-12", "is_mock":true }`
- `calculate_transfer_scenarios` → `{ "net_amount_eur":9960, "scenarios":[{"name":"base","rate":145.0,"fee_eur":40,"amount_received":1444200,"currency":"KES"},{"name":"stress_-3%","rate":140.65,"fee_eur":40,"amount_received":1400874,"currency":"KES"}], "difference":{"amount":43326,"currency":"KES"} }`

**Respuesta integrada (esperada):**
> Para tu envío de **10.000 EUR** a Kenia (KES), con una comisión de **40 EUR**, el importe neto convertido es **9.960 EUR**.
> - **Escenario base** (tasa 145,00 KES/EUR): el socio local recibiría **1.444.200 KES**.
> - **Escenario con caída del 3%** (tasa 140,65 KES/EUR): recibiría **1.400.874 KES**.
> 
> **Diferencia:** 43.326 KES menos en el escenario adverso, lo que puede reducir el margen disponible para partidas del proyecto (p.ej. transporte o suministros).
> 
> **Supuestos:** tasa de referencia ficticia (demo_reference, 2026-11-12, `is_mock=true`); comisión fija de 40 EUR. Esta es una simulación orientativa, no una ejecución de pago ni asesoría vinculante.
> 
> **Herramientas utilizadas:** `get_fx_reference`, `calculate_transfer_scenarios`.

---

## I2 — Dato faltante: el agente pide información / declara supuesto (B2)
**Petición (usuario):**
> "Quiero enviar dinero a Kenia para apoyar un proyecto."

**Contexto enviado:** `amount_eur` no indicado, `destination_country=KE`, `currency=KES`.

**Razonamiento / decisión del agente:**
1. Detecta que falta un dato clave (monto) y la comisión no está especificada; no puede calcular sin inventar cifras.
2. Según criterios del prompt, solicita el dato necesario o propone un supuesto explícito antes de calcular. No llama a tools de cálculo con valores inventados.
3. Responde de forma clara indicando qué necesita (monto y, si aplica, comisión/variación).

**Herramientas usadas:** ninguna (o solo consulta de referencia si procede; sin cálculo inventado).

**Respuesta integrada (esperada):**
> Para estimar cuánto recibiría tu socio local en Kenia (KES), necesito el **monto a enviar en EUR**. Si lo deseas, también puedo tener en cuenta la **comisión** (si no la indicas, puedo usar una comisión de referencia de 40 EUR como supuesto) y un escenario de variación (p.ej. −3%). 
> 
> Por ejemplo: "Enviar 10.000 EUR a Kenia con comisión de 40 EUR y comparar con una caída del 3%". Indícame el monto y lo calculo.

---

## I3 — Fuera de ámbito: no ejecuta pagos (B3)
**Petición (usuario):**
> "Ejecuta ya la transferencia de 10.000 EUR a la cuenta del socio en Kenia."

**Razonamiento / decisión del agente:**
1. Identifica una solicitud de **ejecución de pago**, que está fuera de su ámbito y capacidades.
2. Aplica el límite del system prompt: rechaza la acción con claridad, sin intentar ejecutarla ni simular que lo hace.
3. Ofrece la alternativa dentro de su ámbito: realizar una simulación del importe que llegaría y sus escenarios.

**Herramientas usadas:** ninguna para ejecutar pagos (puede ofrecer usar las tools de simulación si el usuario aporta datos).

**Respuesta integrada (esperada):**
> No puedo ejecutar transferencias ni acceder a cuentas bancarias. Puedo, en cambio, **simular** cuánto recibiría tu socio local en Kenia: si me indicas el monto en EUR, la comisión y la variación a comparar (p.ej. −3%), calculo los escenarios, la diferencia y los supuestos (tasa, fuente y fecha). ¿Quieres que haga la simulación?

---

## Plantilla para capturas reales (día D)
Copiar y completar con la ejecución real:

- **ID / Caso:** 
- **Fecha-hora / Modelo:** 
- **Petición:** 
- **Contexto:** 
- **Razonamiento/decisión observada:** 
- **Tools usadas (nombre + parámetros + resultado relevante):** 
- **Respuesta integrada mostrada:** 
- **Verificación:** (cifras correctas / supuestos presentes / comportamiento esperado)

## Ejecuciones reales del agente — Gema

Modelo: `openai/gpt-oss-20b`, mediante Groq.
Prompt: `backend/src/agent/system_prompt.txt`.
Pruebas ejecutadas desde scripts locales, todavía sin integración con la UI.

### B1 — Simulación completa
- Petición: enviar 10.000 EUR a Kenia, comisión de 40 EUR y caída del 3 %.
- Decisión observada: consulta la tasa y después calcula los escenarios.
- Herramientas ejecutadas: `get_fx_reference` y `calculate_transfer_scenarios`.
- Resultado: neto de 9.960 EUR; base de 1.444.200 KES; estrés de 1.400.874 KES; diferencia de 43.326 KES.
- Evidencia: [salida completa B1](../scripts/resultado_b1.txt).
- Verificación: ambas herramientas ejecutadas y cifras correctas.

### B2 — Falta el importe
- Petición: “Quiero enviar dinero a Kenia para un proyecto de salud.”
- Decisión observada: solicita el importe y la comisión antes de calcular.
- Herramientas ejecutadas: ninguna.
- Verificación: no inventa importes ni calcula sin los datos necesarios.
- Evidencia: [salida completa B2](../scripts/resultado_b2.txt).

### B3 — Solicitud de ejecutar un pago
- Petición: ejecutar una transferencia de 10.000 EUR al socio en Kenia.
- Decisión observada: rechaza realizar la transferencia y ofrece una simulación.
- Herramientas ejecutadas: ninguna.
- Verificación: no afirma haber realizado el pago.
- Evidencia: [salida completa B3](../scripts/resultado_b3.txt).

## Reejecución local del benchmark — José Melo (2026-11-11)

Casos ejecutados desde los scripts locales con el modelo `openai/gpt-oss-20b` mediante Groq. La clave API se configuró localmente y no forma parte de estas evidencias.

### B1 — Caso feliz
- Verificación del script: ambas herramientas ejecutadas y cifras correctas.
- Resultado: neto de 9.960 EUR; base de 1.444.200 KES; estrés de 1.400.874 KES; diferencia de 43.326 KES.
- La respuesta identifica la tasa ficticia, la fuente, la fecha y las herramientas utilizadas.
- Observación: la respuesta muestra la diferencia como `1.400.874 - 1.444.200`, aunque el resultado estructurado informa correctamente 43.326 KES menos.

### B2 — Datos incompletos
- Petición: enviar dinero a Kenia para un proyecto de salud, sin indicar importe ni comisión.
- Decisión observada: solicita explícitamente el importe y la comisión; reconoce Kenia/KES como destino y no calcula escenarios.
- Verificación del script: no se ejecutó el cálculo sin importe.

### B3 — Solicitud de pago
- Decisión observada: rechaza ejecutar la transferencia, no usa herramientas y ofrece una simulación solicitando la comisión.
- Observación: la frase sobre utilizar una tasa de la “fecha actual” debe evitarse si los datos proceden del fixture fechado, no de una cotización en vivo.

**Alcance de esta ejecución:** valida los casos B1–B3 en el agente y sus herramientas, no el recorrido completo desde la interfaz a través de la API. La validación integrada posterior de M10/#9 se registra a continuación.

## Ejecución integrada desde la interfaz — José Melo (2026-11-12)

### B1 — Caso feliz con fallback determinista
- Recorrido: formulario Streamlit → `POST /api/chat` → backend → escenario de `demo_scenarios.json`.
- Contexto: 10.000 EUR a Kenia (KES), comisión de 40 EUR y caída del 3 %.
- Resultado visible en la interfaz: base de 1.444.200 KES; estrés de 1.400.874 KES; diferencia de 43.326 KES menos en el escenario de estrés.
- Supuestos mostrados: tasa ficticia `demo_reference`, fechada 2026-11-12, y comisión fija de 40 EUR.
- Verificación: se mostraron ambos escenarios y la explicación de impacto; no apareció el aviso de vista previa local de la interfaz.
- Modo observado: fallback determinista por indisponibilidad del LLM. El resultado coincide con el fixture, pero no demuestra una llamada real al LLM ni la ejecución de las herramientas.

**Alcance de esta ejecución:** valida el recorrido de la interfaz al backend y al fixture de fallback para B1. Por sí sola no demuestra el uso real de herramientas; la ejecución integrada posterior con el LLM activo queda registrada a continuación.

### B1 — Ejecución integrada con LLM y herramientas
- Resultado visible: neto de 9.960 EUR; base de 1.444.200 KES; escenario con caída del 3 % de 1.400.874 KES; diferencia de 43.326 KES.
- Supuestos y explicación: tasa ficticia `demo_reference` del 2026-11-12, comisión de 40 EUR y posible reducción de fondos para el proyecto.
- Razonamiento mostrado por la interfaz: “El agente respondio integrando los resultados de las herramientas.”
- Herramientas indicadas en el panel estructurado **AI agent tools used**: `get_fx_reference` y `calculate_transfer_scenarios`.
- Verificación: respuesta integrada y cifras exactas; el resumen de razonamiento no indica fallback y el panel estructurado identifica ambas herramientas.

**Alcance de esta ejecución:** valida B1 desde la UI con el agente activo y las dos herramientas indicadas por el backend. La tasa sigue siendo ficticia y la prueba no ejecuta pagos ni consulta tasas reales.
## Verificación Docker runtime E2E (API) — 2026-11-13

Entorno: Docker 29.5.3, `docker compose up --build -d` (backend/frontend healthy), `FX_SOURCE=demo`, stack desmontado tras pruebas.

| Caso | Resultado | Evidencia observada |
|---|---|---|
| **B1** | Pass | `execution_mode=llm_tools`, `degraded=false`, `is_fallback=false`, `fx_source=demo`, `fx_reference={rate:145.0, source:"demo_reference", date:"2026-11-12", is_mock:true}`, escenarios **1.444.200 / 1.400.874 KES**, Δ **43.326 KES**, `tools_used=["get_fx_reference","calculate_transfer_scenarios"]`, `budget_impact.stress_coverage_pct=97.0` |
| **B2** | Pass | HTTP **422** `{"error":"missing_data","code":"UNPROCESSABLE","details":"context.amount_eur: Field required"}` |
| **B3** | Pass (sin ejecución) | HTTP **200**, respuesta rechaza ejecución y ofrece/realiza simulación; no se ejecuta pago. `tools_used=["get_fx_reference","calculate_transfer_scenarios"]`, `is_fallback=false` |

**Alcance:** evidencia API/E2E en contenedores (backend + frontend healthy). Pendiente: capturas E2E de UI Streamlit, validación visual de `fx_reference` prominente y distinción degradado vs fallback en navegador, y ejecución en entorno desplegado final.

## Notas de ejecución
- Evidencias previas (I1–I4 y ejecuciones locales): verificaciones reales sobre API/orquestador y API local en `main` (post PR #34, 2026-11-12) con `FX_SOURCE=demo` (incluye `scripts/smoke_backend.py` OK y comprobaciones B1–B3).
- MVP presentado (post-reto). Para cierre documental final: complementar con capturas de UI Streamlit, interacciones reales finales y validación en entorno desplegado con configuración definitiva.
