import json
import unittest
from pathlib import Path

from backend.src.tools.get_fx_reference import get_fx_reference
from backend.src.tools.calculate_transfer_scenarios import (
    calculate_transfer_scenarios,
)


# Localizamos los datos esperados desde la carpeta de este archivo.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = PROJECT_ROOT / "data" / "processed" / "demo_scenarios.json"


class TestTools(unittest.TestCase):
    """Comprueba las herramientas con los casos de referencia del repo."""

    def test_golden_cases(self):
        # Leemos los resultados esperados, sin modificarlos.
        with FIXTURES_PATH.open(encoding="utf-8") as file:
            cases = json.load(file)

        # Probamos distintos montos, porcentajes y monedas.
        selected_ids = {"B1", "B1b", "B1c", "B4"}
        cases_by_id = {case["id"]: case for case in cases}

        # Evitamos que la prueba pase si falta un caso esperado.
        self.assertTrue(selected_ids.issubset(cases_by_id))

        for case_id in sorted(selected_ids):
            # Cada caso se informa por separado si falla.
            with self.subTest(case=case_id):
                case = cases_by_id[case_id]
                inputs = case["inputs"]
                expected = case["expected"]

                # Primera herramienta: obtener la tasa desde el JSON.
                reference = get_fx_reference(
                    inputs["base"],
                    inputs["quote"],
                )

                # Segunda herramienta: calcular usando la tasa obtenida.
                result = calculate_transfer_scenarios(
                    amount_eur=inputs["amount_eur"],
                    rate=reference["rate"],
                    fee_eur=inputs["fee_eur"],
                    variations=[inputs["variation_pct"]],
                    currency=inputs["quote"],
                )

                self.assertEqual(
                    reference["rate"], expected["reference_rate"]
                )
                self.assertEqual(
                    result["net_amount_eur"], expected["net_amount_eur"]
                )
                self.assertEqual(
                    result["scenarios"], expected["scenarios"]
                )
                self.assertEqual(
                    result["difference"], expected["difference"]
                )

    def test_reference_metadata(self):
        # La herramienta debe conservar los datos de procedencia.
        reference = get_fx_reference("EUR", "KES")

        self.assertEqual(
            set(reference),
            {"rate", "source", "date", "is_mock"},
        )
        self.assertTrue(reference["source"])
        self.assertTrue(reference["date"])
        self.assertIsInstance(reference["is_mock"], bool)

    def test_unknown_currency_pair(self):
        # Si no hay tasa disponible, debe fallar sin inventarla.
        with self.assertRaises(ValueError):
            get_fx_reference("EUR", "XXX")

    def test_fee_exceeds_amount(self):
        # La comisión no puede superar el dinero enviado.
        with self.assertRaises(ValueError):
            calculate_transfer_scenarios(
                100, 145, 150, [-3], currency="KES"
            )


if __name__ == "__main__":
    unittest.main()