"""Middlewares HTTP del backend.

- `RequestContextMiddleware`: asigna/propaga `X-Request-ID`, cronometra cada
  petición y emite un log estructurado con método, ruta, estado y duración.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.src.core.context import new_request_id, set_request_id
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

# Rutas que no aportan valor diagnóstico (sondas de orquestadores).
_QUIET_PATHS = {"/api/health", "/api/ready", "/metrics"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Correlaciona y registra todas las peticiones HTTP."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        set_request_id(request_id)
        request.state.request_id = request_id

        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            path = request.url.path
            if path not in _QUIET_PATHS:
                logger.info(
                    "http_request",
                    extra={
                        "request_id": request_id,
                        "fields": {
                            "method": request.method,
                            "path": path,
                            "status_code": status_code,
                            "duration_ms": duration_ms,
                            "client": request.client.host if request.client else None,
                        },
                    },
                )
            # El contexto es por petición: se limpia al terminar.
            set_request_id(None)
