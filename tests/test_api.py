"""Tests de integración de la API HTTP (contrato público).

Cubre lo que hasta ahora no estaba automatizado (TD-04): endpoints de
salud, validaciones 400/422/429, respuesta 200 con fallback determinista y
cabecera de correlación `X-Request-ID`.
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.src.api import routes
from backend.src.core.rate_limit import RateLimiter
from backend.src.main import app

B1_PAYLOAD = {
    "message": "Quiero enviar 10000 EUR a Kenia, comision 40 EUR",
    "context": {
        "amount_eur": 10000,
        "destination_country": "KE",
        "currency": "KES",
        "fee_eur": 40,
        "scenario_drop_pct": 3,
    },
    "history": [],
}


class TestHealthEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_is_ok(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ready_reports_dependencies(self):
        response = self.client.get("/api/ready")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["status"], {"ready", "degraded"})
        self.assertEqual(body["checks"]["fx_rates.json"], "ok")

    def test_version_is_exposed(self):
        response = self.client.get("/api/version")
        self.assertEqual(response.status_code, 200)
        self.assertIn("version", response.json())

    def test_request_id_header_is_returned(self):
        response = self.client.get("/api/health", headers={"X-Request-ID": "abc123"})
        self.assertEqual(response.headers.get("X-Request-ID"), "abc123")


class TestChatContract(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Cada test usa un limitador limpio.
        routes.rate_limiter.reset()

    def test_empty_message_returns_400(self):
        payload = dict(B1_PAYLOAD)
        payload["message"] = ""
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"], "invalid_input")
        self.assertEqual(body["code"], "BAD_REQUEST")

    def test_unsupported_corridor_returns_400(self):
        payload = dict(B1_PAYLOAD)
        payload["context"] = dict(B1_PAYLOAD["context"])
        payload["context"]["destination_country"] = "GH"
        payload["context"]["currency"] = "GHS"
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_input")

    def test_missing_required_field_returns_422(self):
        payload = dict(B1_PAYLOAD)
        payload["context"] = {"destination_country": "KE", "currency": "KES"}
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"], "missing_data")
        self.assertEqual(body["code"], "UNPROCESSABLE")

    def test_fee_greater_than_amount_returns_400(self):
        payload = dict(B1_PAYLOAD)
        payload["context"] = dict(B1_PAYLOAD["context"])
        payload["context"]["fee_eur"] = 20000
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_too_long_history_returns_400(self):
        payload = dict(B1_PAYLOAD)
        payload["history"] = [{"role": "user", "content": f"mensaje {i}"} for i in range(50)]
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_input")

    def test_rate_limit_returns_429(self):
        original = routes.rate_limiter
        routes.rate_limiter = RateLimiter(limit=1, window_seconds=60)
        try:
            first = self.client.post("/api/chat", json=B1_PAYLOAD)
            second = self.client.post("/api/chat", json=B1_PAYLOAD)
        finally:
            routes.rate_limiter = original
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        body = second.json()
        self.assertEqual(body["error"], "rate_limited")
        self.assertEqual(body["code"], "TOO_MANY_REQUESTS")

    @patch.dict(os.environ, {"FX_SOURCE": "demo"})
    def test_b1_returns_deterministic_fallback_without_llm(self):
        with patch(
            "backend.src.agent.orchestrator._get_llm_client",
            side_effect=RuntimeError("sin clave"),
        ):
            response = self.client.post("/api/chat", json=B1_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        agent = body["agent"]

        self.assertTrue(body["reply"])
        self.assertEqual(agent["execution_mode"], "deterministic_fallback")
        self.assertTrue(agent["degraded"])
        self.assertEqual(agent["tools_used"], [])
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)
        self.assertEqual(agent["scenarios"][1]["amount_received"], 1400874)
        self.assertEqual(agent["difference"]["amount"], 43326)
        self.assertEqual(agent["fx_source"], "demo")
        self.assertEqual(agent["calculation_source"], "demo_scenarios")

    @patch.dict(os.environ, {"FX_SOURCE": "demo"})
    def test_project_budget_is_flagged_as_not_applied(self):
        payload = dict(B1_PAYLOAD)
        payload["context"] = dict(B1_PAYLOAD["context"])
        payload["context"]["project_budget"] = [
            {"name": "Transporte", "amount_local": 320000, "priority": "alta"}
        ]
        with patch(
            "backend.src.agent.orchestrator._get_llm_client",
            side_effect=RuntimeError("sin clave"),
        ):
            response = self.client.post("/api/chat", json=payload)

        self.assertEqual(response.status_code, 200)
        alerts = response.json()["agent"]["alerts"]
        self.assertTrue(any("presupuesto" in a.lower() for a in alerts))


if __name__ == "__main__":
    unittest.main()
