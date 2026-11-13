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

## Funcionalidades incluidas
- **Ejemplos rápidos (B1/B2/B3):** precarga de casos clave (simulación completa, dato faltante, fuera de ámbito) para uso intuitivo.
- **Formulario claro:** mensaje + contexto (monto, país/moneda, comisión, caída %) con acciones de limpiar y comprobación de estado de API (`/api/health`).
- **Consumo de `POST /api/chat`:** manejo de respuestas y errores HTTP/contrato (p. ej. 422) con feedback legible.
- **Trazabilidad y confianza:** `execution_mode`/`degraded`/`is_fallback`, **`fx_reference` prominente** (tasa, fuente, fecha, `is_mock`) y distinción entre fallback determinista y degradado.
- **Resultados útiles para ONGs:** escenarios base/estrés, diferencia potencial, **comparación visual simple**, impacto presupuestario (demo), supuestos, alertas y `tools_used`.
- **Utilidades:** copiar resumen de la simulación e historial local reciente (navegador). Simulación orientativa: sin ejecución de pagos ni cotización firme.

## Notas
- La UI **no ejecuta pagos**; tasas/resultados son de referencia/demo/orientativos.
- El frontend Streamlit (`frontend/`) se mantiene como alternativa/fallback mientras se completa la migración.
- Próximos pasos sugeridos: pulido visual (Figma/tokens), componentes/estado modular, gráficos, tests E2E UI, Docker/deploy estático y CORS/config de entornos.
