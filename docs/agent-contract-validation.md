# Contrato de procedencia del agente

`agent.fx_reference` y `agent.is_fallback` están presentes en todas las respuestas
del orquestador. `fx_reference` solo procede de una ejecución válida de
`get_fx_reference` y contiene exactamente `rate`, `source`, `date`, `is_mock`.
La tasa debe ser positiva y finita; la fuente, no vacía; la fecha, ISO válida;
`is_mock`, booleano. Frankfurter es una referencia FX, no una cotización
ejecutable ni el proveedor del LLM.

| Estado | execution_mode | degraded | is_fallback | fx_reference |
|---|---|---|---|---|
| Normal verificado | llm_tools | false | false | Objeto válido |
| Degradado sin redirección | llm_tools | true | false | Objeto válido si hubo FX, o null |
| Fallback con/sin escenarios | deterministic_fallback | true | true | null siempre |

El flujo degradado sin cálculo no expone escenarios, diferencia ni impacto
presupuestario. Con contexto completo puede redirigirse al fallback y entonces
adopta todos sus campos, sin arrastrar metadatos FX previos.

Los resultados de cálculo y los fixtures de fallback se contrastan con el motor
determinista existente antes de exponer escenarios/diferencia. Cada nuevo intento
FX invalida el cálculo anterior. Un cálculo fallido o incompleto también lo borra.
`budget_impact` sigue siendo opcional: se calcula con escenarios verificados para
KE/KES y presupuesto demo disponible; se conserva en fallback con escenarios.
No se inventan referencias FX a partir de fixtures de escenarios.

El retorno local de la herramienta FX por fallo de Frankfurter no implica por sí
solo `is_fallback=true`: este indicador describe el fallback del orquestador.
Si FX local y cálculo se verifican, el flujo normal puede tener `is_mock=true`
y `is_fallback=false`.
