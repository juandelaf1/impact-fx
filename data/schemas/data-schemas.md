# Esquemas de datos (referencia)

## fx_rates.json (array)
- `base` (string, ISO 4217, req)
- `quote` (string, ISO 4217, req)
- `rate` (number > 0, req)
- `date` (string, ISO 8601, req)
- `source` (string, req) — p.ej. `demo_reference`
- `is_mock` (boolean, req) — debe ser `true` para tasas de demo
- `notes` (string, opc)

## fee_rules.json (array)
- `corridor` (string, req) — ej. `EUR-KES`
- `destination_country` (string, ISO 3166-1 alpha-2, req)
- `type` (string, req) — `fixed` | `percent`
- `value` (number >= 0, req)
- `currency` (string, ISO 4217, req)
- `notes` (string, opc)

## corridors.json (array)
- `origin` (string, ISO 4217, req)
- `origin_country` (string, ISO 3166, opc)
- `destination_country` (string, ISO 3166, req)
- `currency` (string, ISO 4217, req)
- `label` (string, req)
- `demo` (boolean, opc)

## project_budgets.json (array)
- `project_id` (string, req, único)
- `name` (string, req)
- `destination_country` (string, ISO 3166, req)
- `currency` (string, ISO 4217, req)
- `items` (array, req): `{ name: string, amount_local: number >= 0, priority: "alta"|"media"|"baja" }`
- `notes` (string, opc)

## demo_scenarios.json (array)
- `id` (string, req)
- `description` (string, req)
- `inputs` (object, req): `amount_eur, base, quote, destination_country, fee_eur, variation_pct`
- `expected` (object, req): `reference_rate, stressed_rate, net_amount_eur, scenarios[], difference{amount,currency}, assumptions[], tools_used[]`
