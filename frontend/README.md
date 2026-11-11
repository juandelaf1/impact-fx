# Frontend — Impact FX (Streamlit)

Interfaz de usuario en **Streamlit (Python)** para interactuar con el agente y visualizar resultados.

## Responsabilidades
- Formulario de entrada (monto EUR, destino/moneda, comisión, variación %, presupuesto opcional) con validación básica.
- Consumir `POST /api/chat` (y opcionalmente `GET /api/health`) del backend.
- Mostrar respuesta integrada: explicación (`reply`), escenarios, diferencia, supuestos/fuente/fecha/`is_mock`, `tools_used` y alertas (no JSON crudo).
- Gestionar estados de carga y error.

## Estructura sugerida
```text
frontend/
├─ app.py              # entrada principal Streamlit (UI + llamada a API)
├─ requirements.txt    # streamlit, requests, etc.
└─ (opcional) utils/   # helpers de formato/render
```

## Configuración
- `API_BASE_URL` (por defecto `http://localhost:3001`) apuntando al backend. Puede leerse de `.env` o de variables de entorno.

## Ejecución
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```
- App local: `http://localhost:8501`.

## Notas
- Durante desarrollo puede usar datos mock, pero la versión final debe consumir la API real (`/api/chat`).
- Streamlit actúa como cliente de la API REST (separación frontend/backend). Priorizar claridad y demo funcional sobre perfección visual.
