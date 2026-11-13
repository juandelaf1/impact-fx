from decimal import Decimal, InvalidOperation


def _to_decimal(value, field_name: str) -> Decimal:
    """Comprueba que el valor es numérico y lo convierte a Decimal."""

    # Python considera True y False números: los rechazamos.
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{field_name} debe ser un número.")

    try:
        # Decimal evita errores de precisión durante los cálculos.
        # Pasamos por texto para no arrastrar la imprecisión de float.
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} no es un número válido.") from exc

    # No aceptamos valores especiales como infinito o NaN.
    if not number.is_finite():
        raise ValueError(f"{field_name} debe ser un número finito.")

    return number


def calculate_transfer_scenarios(
    amount_eur: float,
    rate: float,
    fee_eur: float,
    variations: list,
    currency: str,
) -> dict:
    """
    Calcula el importe recibido tras descontar la comisión.

    Parámetros:
        amount_eur: importe enviado en euros.
        rate: unidades de moneda destino por cada euro.
        fee_eur: comisión descontada en euros.
        variations: porcentajes de cambio de la tasa, por ejemplo [-3].
        currency: moneda de destino, por ejemplo "KES" o "GHS".

    Devuelve:
        Importe neto en euros, escenarios y diferencia.

    En el MVP admitimos una única variación para comparar
    dos escenarios: base y variación. La salida del contrato
    solo contempla una diferencia.
    """

    # Validamos y convertimos las entradas para calcular con precisión.
    amount = _to_decimal(amount_eur, "amount_eur")
    reference_rate = _to_decimal(rate, "rate")
    fee = _to_decimal(fee_eur, "fee_eur")

    if amount <= 0:
        raise ValueError("El monto debe ser mayor que cero.")

    if reference_rate <= 0:
        raise ValueError("La tasa debe ser mayor que cero.")

    if fee < 0:
        raise ValueError("La comisión no puede ser negativa.")

    if fee > amount:
        raise ValueError("La comisión no puede superar el monto enviado.")

    # La moneda se recibe como parámetro: no fijamos KES en el código.
    if not isinstance(currency, str):
        raise ValueError("La moneda debe ser una cadena de texto.")

    currency = currency.strip().upper()

    # Validamos el formato de tres letras.
    # Esto no comprueba que exista en el catálogo oficial de monedas.
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise ValueError("La moneda debe tener tres letras, por ejemplo KES.")

    # Limitamos el MVP a una variación para evitar una diferencia ambigua.
    if not isinstance(variations, list) or len(variations) != 1:
        raise ValueError("Indica una única variación, por ejemplo [-3].")

    variation = _to_decimal(variations[0], "variations[0]")

    # Una caída del 100 % o mayor produciría una tasa nula o negativa.
    if variation <= -100:
        raise ValueError("La variación debe ser mayor que -100 %.")

    # La comisión se descuenta antes de convertir a moneda local.
    # Ejemplo: 10000 - 40 = 9960 EUR.
    net_amount = amount - fee

    # Escenario base: importe neto multiplicado por la tasa de referencia.
    base_received = net_amount * reference_rate

    # Escenario con variación:
    # 145 × (1 + (-3 / 100)) = 140.65 KES por EUR.
    scenario_rate = reference_rate * (Decimal("1") + variation / Decimal("100"))
    scenario_received = net_amount * scenario_rate

    # Positiva: llega menos dinero que en el escenario base.
    # Negativa: llega más dinero que en el escenario base.
    difference = base_received - scenario_received

    # Evitamos nombres como "stress_-3.0%": usamos "stress_-3%".
    variation_label = format(variation.normalize(), "f")

    # Convertimos a float únicamente al preparar la respuesta,
    # para que pueda enviarse como JSON desde el backend.
    return {
        "net_amount_eur": float(net_amount),
        "scenarios": [
            {
                "name": "base",
                "rate": float(reference_rate),
                "fee_eur": float(fee),
                "amount_received": float(base_received),
                "currency": currency,
            },
            {
                "name": f"stress_{variation_label}%",
                "rate": float(scenario_rate),
                "fee_eur": float(fee),
                "amount_received": float(scenario_received),
                "currency": currency,
            },
        ],
        "difference": {
            "amount": float(difference),
            "currency": currency,
        },
    }
