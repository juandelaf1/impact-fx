import os

import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_BASE_URL = (
    os.getenv("API_BASE_URL")
    or os.getenv("VITE_API_BASE_URL")
    or "http://localhost:3001"
).rstrip("/")

API_TIMEOUT = 30


class APIError(Exception):
    """Error controlado al comunicarse con el backend."""


def send_chat_message(message: str, context: dict, history: list | None = None) -> dict:
    """
    Envía los datos de una transferencia al agente de Impact FX
    y devuelve su respuesta estructurada.
    """

    url = f"{API_BASE_URL}/api/chat"

    payload = {
        "message": message,
        "context": context,
        "history": history or []
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=API_TIMEOUT
        )

        if response.status_code >= 400:
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"detail": response.text}

            raise APIError(
                f"Error del backend ({response.status_code}): "
                f"{error_data}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise APIError("El backend ha devuelto una respuesta no válida.") from exc

        if not isinstance(data, dict):
            raise APIError("El formato de respuesta del backend no es válido.")

        if "reply" not in data:
            raise APIError("La respuesta del backend no contiene el campo 'reply'.")

        return data

    except requests.exceptions.Timeout as exc:
        raise APIError(
            "El backend ha tardado demasiado en responder."
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        raise APIError(
            "No se ha podido conectar con el backend. "
            "Comprueba que el servidor está funcionando."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise APIError(
            f"Error durante la comunicación con el backend: {exc}"
        ) from exc


def check_api_health() -> bool:
    """Comprueba si el backend está disponible."""

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/health",
            timeout=5
        )

        return (
            response.status_code == 200
            and response.json().get("status") == "ok"
        )

    except (
        requests.exceptions.RequestException,
        ValueError,
        AttributeError
    ):
        return False
