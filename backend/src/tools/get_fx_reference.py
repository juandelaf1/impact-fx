import json
from pathlib import Path

# Localizamos la raíz del proyecto desde este archivo:
# parents[0] → tools
# parents[1] → src
# parents[2] → backend
# parents[3] → impact-fx
#
# Así podemos encontrar los datos aunque ejecutemos Python
# desde una carpeta distinta.
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


def get_fx_reference(
    base: str,
    quote: str,
    date: str | None = None,
) -> dict:
    """
    Busca una tasa de cambio en los datos locales de la demo.

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

    # Abrimos el JSON en modo lectura.
    # "with" cierra el archivo automáticamente al terminar.
    with (DATA_DIR / "fx_rates.json").open(encoding="utf-8") as file:
        # Convertimos el contenido JSON en una lista de diccionarios.
        rates = json.load(file)

    # Guardamos las tasas que coinciden con las monedas solicitadas.
    matches = []

    for item in rates:
        same_currencies = (
            item["base"] == base
            and item["quote"] == quote
        )

        # Si no se pide fecha, aceptamos cualquier fecha disponible.
        # Si se pide una, exigimos coincidencia exacta.
        valid_date = date is None or item["date"] == date

        if same_currencies and valid_date:
            matches.append(item)

    # Si no hay coincidencias, informamos del problema.
    # Nunca inventamos una tasa ni usamos otro par de monedas.
    if not matches:
        raise ValueError(
            f"No hay tasa de referencia para {base}/{quote}"
            + (f" en {date}." if date else ".")
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