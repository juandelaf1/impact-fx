# Datos — Impact FX

## Objetivo
Proveer datos **deterministas, limpios y trazables** para que el agente y la UI funcionen sin depender de APIs externas en la demo.

## Estructura
- `raw/`: fuentes originales (si se usan) y notas de procedencia.
- `processed/`: **fuente de verdad** para la demo (JSON listos para consumir).
- `schemas/`: esquemas de referencia para validación.

## Archivos procesados
| Archivo | Descripción | Campos clave |
|---|---|---|
| `fx_rates.json` | Tasas de referencia por par | `base, quote, rate, date, source, is_mock` |
| `fee_rules.json` | Reglas de comisión por corredor | `corridor, type, value, currency, notes` |
| `corridors.json` | Corredores soportados | `origin, destination_country, currency, label` |
| `project_budgets.json` | Presupuestos de ejemplo por partidas (moneda local) | `project_id, destination_country, currency, items[{name, amount_local, priority}]` |
| `demo_scenarios.json` | Golden cases (inputs + resultados esperados) | `id, description, inputs, expected` |

## Reglas de limpieza y normalización
- **Monedas/países:** códigos ISO 4217 / ISO 3166. **Fechas:** ISO 8601.
- **Importes:** numéricos (sin símbolos), decimales consistentes.
- **Trazabilidad:** toda tasa incluye `source`, `date` e `is_mock` (las tasas de demo son ficticias y deben mostrarse como tales).
- **Calidad:** sin duplicados, sin nulos críticos, totales coherentes, golden cases verificados.

## Golden case (verificado)
- 10.000 EUR → KES, fee 40 EUR, tasa 145 KES/EUR, variación −3%.
- Neto: 9.960 EUR. Base: 9.960 × 145 = **1.444.200 KES**. Estrés (140,65): **1.400.874 KES**. Δ **43.326 KES**.

## Supuestos y ética
- Tasas y comisiones de demo son **de referencia/ficticias** (no cotización vinculante). Se etiquetan explícitamente.
- Presupuestos curados/sintéticos y plausibles; **sin datos personales o sensibles reales**.
- Uso orientativo (simulación), no ejecución de pagos ni asesoría financiera/legal vinculante.
