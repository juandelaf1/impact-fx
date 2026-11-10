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
