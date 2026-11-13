import json
import math
import os
import re
import time
import warnings
from datetime import date as calendar_date
from http.client import HTTPException
from pathlib import Path
from threading import Lock
from urllib.request import urlopen

# Localizamos la raíz del proyecto desde este archivo:
# parents[0] → tools
# parents[1] → src
# parents[2] → backend
# parents[3] → impact-fx
#
# Así podemos encontrar los datos aunque ejecutemos Python
# desde una carpeta distinta.
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"

# Caché/circuit breaker en memoria para consultas live (Frankfurter).
# Por defecto desactivados (TTL=0, threshold=0) para preservar comportamiento
# determinista y compatibilidad con tests existentes.
_FX_CACHE: dict[tuple[str, str], tuple[float, dict]] = {}
_FX_CB_FAILURES = 0
_FX_CB_OPEN_UNTIL = 0.0
_FX_LOCK = Lock()


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _fx_cache_ttl_seconds() -> int:
    return max(0, _env_int("FX_CACHE_TTL_SECONDS", 0))


def _fx_cb_failure_threshold() -> int:
    return max(0, _env_int("FX_CIRCUIT_BREAKER_FAILURE_THRESHOLD", 0))


def _fx_cb_cooldown_seconds() -> int:
    return max(0, _env_int("FX_CIRCUIT_BREAKER_COOLDOWN_SECONDS", 30))


def reset_fx_runtime_state() -> None:
    """Limpia caché y estado del circuit breaker (útil en tests/procesos)."""

    global _FX_CB_FAILURES, _FX_CB_OPEN_UNTIL
    with _FX_LOCK:
        _FX_CACHE.clear()
        _FX_CB_FAILURES = 0
        _FX_CB_OPEN_UNTIL = 0.0


def _cache_get(base: str, quote: str) -> dict | None:
    ttl = _fx_cache_ttl_seconds()
    if ttl <= 0:
        return None
    key = (base, quote)
    now = time.monotonic()
    with _FX_LOCK:
        entry = _FX_CACHE.get(key)
        if not entry:
            return None
        expires_at, payload = entry
        if expires_at <= now:
            _FX_CACHE.pop(key, None)
            return None
        return dict(payload)


def _cache_set(base: str, quote: str, payload: dict) -> None:
    ttl = _fx_cache_ttl_seconds()
    if ttl <= 0:
        return
    with _FX_LOCK:
        _FX_CACHE[(base, quote)] = (time.monotonic() + ttl, dict(payload))


def _cb_allow_call() -> bool:
    threshold = _fx_cb_failure_threshold()
    if threshold <= 0:
        return True
    now = time.monotonic()
    with _FX_LOCK:
        if _FX_CB_OPEN_UNTIL > now:
            return False
        if _FX_CB_OPEN_UNTIL and _FX_CB_OPEN_UNTIL <= now:
            # Fin de cooldown: permitir intento de half-open implícito.
            _FX_CB_OPEN_UNTIL = 0.0
            _FX_CB_FAILURES = 0
    return True


def _cb_record_success() -> None:
    global _FX_CB_FAILURES, _FX_CB_OPEN_UNTIL
    threshold = _fx_cb_failure_threshold()
    if threshold <= 0:
        return
    with _FX_LOCK:
        _FX_CB_FAILURES = 0
        _FX_CB_OPEN_UNTIL = 0.0


def _cb_record_failure() -> None:
    global _FX_CB_FAILURES, _FX_CB_OPEN_UNTIL
    threshold = _fx_cb_failure_threshold()
    if threshold <= 0:
        return
    with _FX_LOCK:
        _FX_CB_FAILURES += 1
        if _FX_CB_FAILURES >= threshold:
            _FX_CB_OPEN_UNTIL = time.monotonic() + _fx_cb_cooldown_seconds()


def fetch_frankfurter_rate(base: str, quote: str) -> dict:
    """
    Consulta el último tipo de cambio de referencia disponible
    en Frankfurter.
    """
    url = f"https://api.frankfurter.dev/v2/rate/{base}/{quote}"

    try:
        with urlopen(url, timeout=8) as response:
            data = json.load(response)
    except (OSError, HTTPException) as error:
        raise ConnectionError("No se pudo consultar Frankfurter.") from error

    try:
        if not isinstance(data, dict):
            raise ValueError("La respuesta debe ser un objeto JSON.")
        raw_rate = data["rate"]
        if isinstance(raw_rate, bool):
            raise ValueError("La tasa no puede ser un booleano.")
        rate = float(raw_rate)
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("La tasa debe ser positiva y finita.")
        rate_date = data["date"]
        if not isinstance(rate_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rate_date):
            raise ValueError("La fecha debe tener formato YYYY-MM-DD.")
        calendar_date.fromisoformat(rate_date)
        if data.get("base") != base or data.get("quote") != quote:
            raise ValueError("El par de monedas no coincide con la consulta.")
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError("Frankfurter devolvió una referencia no válida.") from error

    return {
        "rate": rate,
        "source": "frankfurter",
        "date": rate_date,
        "is_mock": False,
    }


def get_fx_reference(
    base: str,
    quote: str,
    date: str | None = None,
) -> dict:
    """
    Busca una tasa local o de Frankfurter según FX_SOURCE (demo por defecto).
    En modo live, hoy o sin fecha consulta la última referencia publicada.
    Las demás fechas utilizan los datos locales.

    Parámetros:
        base: moneda de origen, por ejemplo "EUR".
        quote: moneda de destino, por ejemplo "KES".
        date: fecha opcional, por ejemplo "2026-11-12".
              Si no se indica, usamos la última fecha disponible.

    Devuelve:
        Un diccionario con la tasa, fuente, fecha y un indicador
        que informa de si el dato es ficticio.

    Si no encuentra la tasa o los parámetros son incorrectos,
    lanza ValueError para que el backend gestione el error.
    """

    # Comprobamos los tipos antes de intentar limpiar los textos.
    if not isinstance(base, str) or not isinstance(quote, str):
        raise ValueError("Las monedas deben ser cadenas de texto.")

    # Aceptamos entradas como " eur " y las convertimos en "EUR".
    base = base.strip().upper()
    quote = quote.strip().upper()

    # No podemos buscar una tasa si falta alguna moneda.
    if not base or not quote:
        raise ValueError("Debes indicar las monedas de origen y destino.")

    # La fecha puede omitirse, pero si llega debe ser texto.
    if date is not None and not isinstance(date, str):
        raise ValueError("La fecha debe ser una cadena de texto.")

    if not re.fullmatch(r"[A-Z]{3}", base) or not re.fullmatch(r"[A-Z]{3}", quote):
        raise ValueError("Las monedas deben tener tres letras, por ejemplo EUR.")

    fx_source = os.getenv("FX_SOURCE", "demo").strip().lower()
    if fx_source not in {"demo", "live"}:
        raise ValueError("FX_SOURCE debe ser demo o live.")

    # En modo live, hoy y sin fecha consultan la última referencia publicada.
    # Conservamos su fecha real, que puede ser anterior a hoy.
    if fx_source == "live" and (date is None or date == calendar_date.today().isoformat()):
        cached = _cache_get(base, quote)
        if cached is not None:
            return cached

        if not _cb_allow_call():
            warnings.warn(
                "Frankfurter no disponible: circuito abierto temporalmente (circuit breaker). "
                "Se intentarán usar datos ficticios de demostración.",
                RuntimeWarning,
                stacklevel=2,
            )
        else:
            try:
                # Consultamos la API externa.
                result = fetch_frankfurter_rate(base, quote)
                _cb_record_success()
                _cache_set(base, quote, result)
                return result

            # Si la API falla, capturamos el error.
            except (ConnectionError, ValueError) as error:
                _cb_record_failure()
                # Mostramos una advertencia en la terminal.
                warnings.warn(
                    f"Frankfurter no disponible: {error}. "
                    "Se intentarán usar datos ficticios de demostración.",
                    RuntimeWarning,
                    stacklevel=2,
                )

            # Continuamos con el JSON local, que devuelve
            # is_mock=True para identificar los datos ficticios.

    # Abrimos el JSON en modo lectura.
    # "with" cierra el archivo automáticamente al terminar.
    with (DATA_DIR / "fx_rates.json").open(encoding="utf-8") as file:
        # Convertimos el contenido JSON en una lista de diccionarios.
        rates = json.load(file)

    # Guardamos las tasas que coinciden con las monedas solicitadas.
    matches = []

    for item in rates:
        same_currencies = item["base"] == base and item["quote"] == quote

        # Si no se pide fecha, aceptamos cualquier fecha disponible.
        # Si se pide una, exigimos coincidencia exacta.
        valid_date = date is None or item["date"] == date

        if same_currencies and valid_date:
            matches.append(item)

    # Si no hay coincidencias, informamos del problema.
    # Nunca inventamos una tasa ni usamos otro par de monedas.
    if not matches:
        raise ValueError(
            f"No hay tasa de referencia para {base}/{quote}" + (f" en {date}." if date else ".")
        )

    # Elegimos la tasa más reciente entre las coincidencias.
    # Las fechas del fixture usan YYYY-MM-DD, que permite
    # compararlas como texto manteniendo el orden cronológico.
    reference = max(matches, key=lambda item: item["date"])

    # Devolvemos exactamente los campos acordados en el contrato.
    # is_mock=True significa que la tasa es ficticia para la demo.
    return {
        "rate": reference["rate"],
        "source": reference["source"],
        "date": reference["date"],
        "is_mock": reference["is_mock"],
    }
