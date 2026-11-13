# Frontend — Impact FX (Streamlit)

Interfaz de usuario en **Streamlit (Python)** para interactuar con el agente y visualizar resultados.

## Responsabilidades

- Formulario de entrada (monto EUR, destino/moneda, comisión, variación %, presupuesto opcional) con validación básica.
- Consumir `POST /api/chat` (y `GET /api/health` como sonda) del backend.
- Mostrar la respuesta integrada: explicación (`reply`), escenarios, diferencia, supuestos/fuente/fecha/`is_mock`, `tools_used` y alertas (nunca JSON crudo de las tools).
- Gestionar estados de carga y error, incluido el aviso de límite de tasa (429) y el preview local cuando el backend no responde.

## Estructura

```text
frontend/
├── app.py                     # entrada principal Streamlit (UI + llamada a API)
├── components/
│   └── results_panel.py        # escenarios, diferencia, gráficos y trazabilidad
├── services/
│   ├── api.py                 # cliente HTTP (sesión, reintentos, errores tipados)
│   └── demo_data.py           # preview local cuando el backend no está disponible
└── styles/custom.css
```

> Las dependencias del frontend viven en el lockfile de la raíz (`requirements.txt`), no en `frontend/`.

## Configuración

- `API_BASE_URL` (por defecto `http://localhost:3001`) apuntando al backend. Puede leerse de `.env` o de variables de entorno.
- `API_TIMEOUT` (por defecto `60`): debe ser ≥ al timeout del proveedor LLM en el backend.

## Ejecución

```bash
pip install -r requirements.txt          # desde la raíz del repo
streamlit run frontend/app.py
```

- App local: `http://localhost:8501`.

## Tests y calidad

```bash
pytest tests/test_frontend_services.py -q
ruff check frontend
```

## Notas

- Durante el desarrollo puede usarse el preview local, pero la versión final consume la API real (`/api/chat`).
- Streamlit actúa como cliente de la API REST (separación frontend/backend).
- Todo valor interpolado en HTML se escapa (`html.escape`) antes de renderizarlo.
- Pendiente: cubrir la UI con `streamlit.testing.v1.AppTest` (ver `docs/backlog.md`, P2.5).
