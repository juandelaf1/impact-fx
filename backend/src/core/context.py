"""Contexto de petición compartido (request_id) para correlación de logs.

Se usa `contextvars` porque FastAPI ejecuta las rutas en un thread pool: el
valor debe viajar con la petición, no con el hilo.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_REQUEST_ID: ContextVar[str | None] = ContextVar("impact_fx_request_id", default=None)


def new_request_id() -> str:
    """Genera un identificador de petición (UUID4 hex)."""

    return uuid.uuid4().hex


def set_request_id(request_id: str | None) -> None:
    """Fija el request_id del contexto actual."""

    _REQUEST_ID.set(request_id)


def current_request_id() -> str | None:
    """Devuelve el request_id del contexto actual (o None)."""

    return _REQUEST_ID.get()


def reset_request_id() -> None:
    """Limpia el request_id del contexto actual."""

    _REQUEST_ID.set(None)
