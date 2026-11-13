# Impact FX — Frontend (Vite)

Nueva interfaz web para Impact FX construida con **Vite + React + TypeScript + Tailwind CSS**.

> Recomendación de stack: equilibrio entre ligereza/velocidad de desarrollo (Vite), ecosistema y compatibilidad laboral (React + TS) y productividad de UI (Tailwind). Para este caso de uso (dashboard interactivo que consume la API FastAPI) no es necesario SSR/SEO de Next.js.

## Requisitos
- Node.js + npm
- Backend de Impact FX en ejecución (por defecto `http://127.0.0.1:3001`)

## Configuración
Copia `.env.example` a `.env` si necesitas cambiar la API:

```bash
cp .env.example .env
# VITE_API_BASE_URL=http://127.0.0.1:3001
```

## Desarrollo

```bash
npm install
npm run dev
```

## Build de producción

```bash
npm run build
npm run preview
```

## Funcionalidades incluidas (MVP UI)
- Formulario de simulación (`message` + contexto: monto, país/moneda, comisión, caída %).
- Consumo de `POST /api/chat` y manejo de errores HTTP/contrato.
- Visualización de respuesta integrada, `execution_mode`/`degraded`/`is_fallback`.
- **`fx_reference` prominente** (tasa, fuente, fecha, `is_mock`) y distinción fallback determinista vs degradado.
- Escenarios, diferencia, impacto presupuestario (demo), supuestos, alertas y `tools_used`.

## Notas
- La UI **no ejecuta pagos**; tasas/resultados son de referencia/demo/orientativos.
- El frontend Streamlit (`frontend/`) se mantiene como alternativa/fallback mientras se completa la migración.
- Próximos pasos sugeridos: pulido visual (Figma/tokens), componentes/estado modular, gráficos, tests E2E UI, Docker/deploy estático y CORS/config de entornos.
