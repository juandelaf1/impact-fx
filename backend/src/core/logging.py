"""Logging estructurado (JSON) para el backend.

Objetivos:
- Cada evento de negocio va acompañado de un `request_id` para correlación.
- En producción (`LOG_FORMAT=json`) se emite una línea JSON por evento, lista
  para ingestas en Loki/ELK/Datadog.
- En local (`LOG_FORMAT=text`) se mantiene una salida legible.

Uso:
    from backend.src.core.logging import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)
    logger.info("simulacion_completada", extra={"fields": {...}})
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

_RESERVED = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Formatea los registros como una línea JSON por evento."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            for key, value in fields.items():
                if key not in _RESERVED:
                    payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class ContextFilter(logging.Filter):
    """Inyecta el `request_id` del contexto asyncio en cada registro."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            try:
                from backend.src.core.context import current_request_id

                record.request_id = current_request_id()
            except Exception:  # pragma: no cover - defensivo
                record.request_id = None
        return True


def configure_logging(level: str | None = None, fmt: str | None = None) -> None:
    """Configura el logging raíz del proceso (idempotente)."""

    level_name = (level or "INFO").upper()
    log_format = (fmt or "json").lower()

    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level_name)

    # uvicorn duplica los accesos si tiene sus propios handlers.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True

    if not any(isinstance(f, ContextFilter) for f in handler.filters):
        handler.addFilter(ContextFilter())


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el filtro de contexto aplicado."""

    logger = logging.getLogger(name)
    if not any(isinstance(f, ContextFilter) for f in logger.filters):
        logger.addFilter(ContextFilter())
    return logger
