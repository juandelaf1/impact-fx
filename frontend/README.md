# Frontend — Impact FX

Interfaz de usuario para interactuar con el agente y visualizar resultados.

## Responsabilidades
- Formulario de entrada (monto EUR, destino/moneda, comisión, variación %, presupuesto opcional) con validación básica.
- Consumir `POST /api/chat` (y opcionalmente `GET /api/health`).
- Mostrar respuesta integrada: explicación (`reply`), escenarios, diferencia, supuestos/fuente/fecha/`is_mock`, `tools_used` y alertas (no JSON crudo).
- Gestionar estados de carga y error.

## Estructura sugerida
```text
frontend/src/
├─ components/  # formulario, tarjetas/tabla de escenarios, alertas, estado
├─ services/    # cliente API (fetch)
├─ styles/
└─ main.*
```

## Configuración
- `VITE_API_BASE_URL` (o equivalente) apuntando al backend (ver `.env.example`).

## Ejecución (completar según stack elegido)
```bash
# instalar dependencias
# npm run dev
```

## Notas
- Durante desarrollo puede usar datos mock, pero la versión final debe consumir la API real.
- Priorizar claridad y demo funcional sobre perfección visual.
