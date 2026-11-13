import os
import time

import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_BASE_URL = (
    os.getenv("API_BASE_URL") or os.getenv("VITE_API_BASE_URL") or "http://localhost:3001"
).rstrip("/")

# El backend puede tardar hasta ~50 s (LLM + reintentos) antes de responder.
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))
HEALTH_TIMEOUT = 5
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 1.0

# Sesión reutilizable: mantiene el pool de conexiones entre peticiones.
_session = requests.Session()


class APIError(Exception):
    """Error controlado al comunicarse con el backend."""

    def __init__(
        self, message: str, status_code: int | None = None, error_data: dict | None = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_data = error_data or {}


def _friendly_error(status_code: int, error_data: dict) -> str:
    details = ""
    if isinstance(error_data, dict):
        details = str(error_data.get("details") or error_data.get("detail") or "").strip()
    if status_code == 400:
        return details or "Entrada inválida. Revisa los datos e inténtalo de nuevo."
    if status_code == 422:
        # B2: dato faltante / request no procesable -> solicitar dato faltante sin inventar cifras
        return details or "Faltan datos para completar la simulación. Indica el dato faltante."
    if status_code == 429:
        return (
            details
            or "Has alcanzado el límite de peticiones. Espera unos segundos e inténtalo de nuevo."
        )
    if status_code == 502:
        return details or "El servicio no está disponible temporalmente. Inténtalo de nuevo."
    return details or f"Error del backend ({status_code})."


def send_chat_message(message: str, context: dict, history: list | None = None) -> dict:
    """
    Envía los datos de una transferencia al agente de Impact FX
    y devuelve su respuesta estructurada.

    Reintenta ante fallos de conexión (no ante errores HTTP: un 400/422
    es una respuesta válida y debe mostrarse al usuario tal cual).
    """

    url = f"{API_BASE_URL}/api/chat"

    payload = {"message": message, "context": context, "history": history or []}

    last_connection_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = _session.post(url, json=payload, timeout=API_TIMEOUT)
        except requests.exceptions.Timeout as exc:
            raise APIError(
                "El backend ha tardado demasiado en responder (timeout).",
                error_data={"code": "TIMEOUT"},
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            last_connection_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
            raise APIError(
                "No se ha podido conectar con el backend. Comprueba que el servidor está funcionando.",
                error_data={"code": "CONNECTION_ERROR"},
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise APIError(
                "Error durante la comunicación con el backend.",
                error_data={"details": "request_error"},
            ) from exc

        if response.status_code >= 400:
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"detail": response.text}
            raise APIError(
                _friendly_error(
                    response.status_code, error_data if isinstance(error_data, dict) else {}
                ),
                status_code=response.status_code,
                error_data=error_data
                if isinstance(error_data, dict)
                else {"detail": str(error_data)},
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise APIError(
                "El backend ha devuelto una respuesta no válida.",
                status_code=response.status_code,
            ) from exc

        if not isinstance(data, dict):
            raise APIError(
                "El formato de respuesta del backend no es válido.",
                status_code=response.status_code,
            )

        if "reply" not in data:
            raise APIError(
                "La respuesta del backend no contiene el campo 'reply'.",
                status_code=response.status_code,
            )

        return data

    raise APIError(  # pragma: no cover - salvaguarda
        "No se ha podido conectar con el backend.",
        error_data={"code": "CONNECTION_ERROR"},
    ) from last_connection_error


def check_api_health() -> bool:
    """Comprueba si el backend está disponible."""

    try:
        response = _session.get(f"{API_BASE_URL}/api/health", timeout=HEALTH_TIMEOUT)

        return response.status_code == 200 and response.json().get("status") == "ok"

    except (requests.exceptions.RequestException, ValueError, AttributeError):
        return False
