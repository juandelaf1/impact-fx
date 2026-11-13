"""Limitador de tasa en memoria (ventana deslizante).

Protege el endpoint `/api/chat` frente a abuso: sin autenticación, cada
petición puede consumir créditos del proveedor LLM.

Notas de diseño:
- Implementación en memoria y por proceso: suficiente para un despliegue de
  una sola instancia. Con varias réplicas, hay que sustituir por un backend
  compartido (Redis) manteniendo la misma interfaz.
- Ventana deslizante exacta: se guardan los timestamps de las peticiones
  admitidas y se descartan los que caen fuera de la ventana.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitResult:
    """Resultado de una comprobación de límite de tasa."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    reset_after: int


class RateLimiter:
    """Limitador de tasa por clave (por defecto, IP de cliente)."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        if limit <= 0:
            raise ValueError("limit debe ser mayor que cero")
        if window_seconds <= 0:
            raise ValueError("window_seconds debe ser mayor que cero")
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> RateLimitResult:
        """Comprueba (y consume) una petición para la clave indicada."""

        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self.window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.limit:
                retry_after = max(1, int(hits[0] + self.window_seconds - timestamp) + 1)
                return RateLimitResult(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    retry_after=retry_after,
                    reset_after=retry_after,
                )

            hits.append(timestamp)
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=self.limit - len(hits),
                retry_after=0,
                reset_after=int(self.window_seconds),
            )

    def reset(self) -> None:
        """Vacía el estado (útil en tests y en el arranque de la app)."""

        with self._lock:
            self._hits.clear()
