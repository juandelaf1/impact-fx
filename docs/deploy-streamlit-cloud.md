# Despliegue del frontend en Streamlit Community Cloud

Esta guía describe cómo publicar **solo el frontend Streamlit** de Impact FX en Streamlit Community Cloud.

> **Importante:** el MVP completo requiere un backend FastAPI (`/api/chat`, `/api/health`) desplegado aparte. Si no configuras un backend accesible, la app puede funcionar en **preview local/demo** (ilustrativo, sin ejecución real de backend/tools/LLM).

## 1) Requisitos previos
- Repositorio en GitHub con este código.
- Cuenta en [Streamlit Community Cloud](https://streamlit.io/cloud).
- (Para flujo integrado real) Backend FastAPI desplegado y accesible por HTTPS (p. ej. Render, Railway, Fly.io, Cloud Run, VPS).

## 2) Crear la app en Streamlit Cloud
1. En Streamlit Community Cloud: **Create app** (o *New app*).
2. Selecciona:
   - **Repository:** `juandelaf1/impact-fx` (o tu fork)
   - **Branch:** `main` (o la rama que quieras publicar)
   - **Main file path:** `streamlit_app.py` (recomendado, wrapper en raíz) o `frontend/app.py`
3. (Opcional) Elige la versión de Python compatible (recomendado 3.11, coherente con el proyecto).
4. Despliega.

## 3) Dependencias
- Streamlit Cloud instala paquetes desde el `requirements.txt` del repositorio (raíz). Este repo incluye dependencias necesarias para el frontend (`streamlit`, `requests`, `python-dotenv`, `plotly`, etc.).

## 4) Configuración (Secrets / variables)
En **App settings → Secrets** configura al menos:

```toml
API_BASE_URL = "https://tu-backend.example.com"
```

- `API_BASE_URL`: URL base del backend FastAPI (sin `/api/chat` al final). El frontend llamará a `API_BASE_URL/api/health` y `API_BASE_URL/api/chat`.
- Si **no** defines un backend disponible, la app mostrará el comportamiento de fallback/preview local según disponibilidad (demo ilustrativo).

> Nota: no incluyas claves ni `.env` en el repositorio. Si en el futuro usas secretos adicionales en frontend, añádelos en Secrets.

## 5) Configuración del backend (para demo integrada real)
Si conectas un backend externo:
- Define `CORS_ORIGIN` en el backend para permitir el dominio de Streamlit Cloud (p. ej. `https://<tu-app>.streamlit.app`).
- Usa `FX_SOURCE=demo` para resultados deterministas de demo.
- Configura variables LLM (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, etc.) si deseas flujo `llm_tools`; sin LLM válido, el backend puede responder en fallback determinista cuando aplique.
- Verifica `GET /api/health` y `POST /api/chat` desde el entorno desplegado.

## 6) Verificación rápida tras desplegar
- La app carga correctamente (UI Streamlit).
- Con backend configurado y accesible: caso B1 muestra resultados coherentes (1.444.200 / 1.400.874 / Δ 43.326 KES) y metadatos de ejecución.
- Sin backend: se muestra preview local/demo (no confundir con fallback determinista del backend/agente).
- Casos de error: B2 (dato faltante) y B3 (no ejecución de pago) deben comportarse según contrato/UI disponible.

## 7) Limitaciones
- Streamlit Cloud **no** ejecuta el backend FastAPI de este repositorio; es solo para el frontend.
- Tasas y resultados del MVP son **de referencia/demo** (no cotización firme ni ejecución de pagos).
- Pueden existir cold starts/timeouts según el backend y la plataforma.

## Referencias
- [README](../README.md)
- [Contrato API](api-contract.md)
- [Guion de demo](demo-script.md)
- [Benchmark](benchmark.md)
