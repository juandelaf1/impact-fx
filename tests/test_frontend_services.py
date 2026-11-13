"""Tests de los servicios del frontend (cliente API y preview local).

El frontend no era una capa sin cubrir: estos tests fijan el contrato que
el backend expone y el modo de demostración local.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import requests

from frontend.services import api as api_client
from frontend.services.demo_data import get_demo_response


def _response(status_code: int, payload: dict | None = None, text: str = ""):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.json = MagicMock(return_value=payload if payload is not None else {})
    return response


class TestApiClient(unittest.TestCase):
    def test_send_chat_message_returns_payload(self):
        payload = {"reply": "ok", "agent": {"execution_mode": "llm_tools"}}
        session = MagicMock()
        session.post.return_value = _response(200, payload)

        with patch.object(api_client, "_session", session):
            result = api_client.send_chat_message("hola", {"amount_eur": 10000})

        self.assertEqual(result, payload)
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(session.post.call_args.kwargs["json"]["message"], "hola")

    def test_send_chat_message_raises_api_error_on_400(self):
        session = MagicMock()
        session.post.return_value = _response(
            400,
            {"error": "invalid_input", "code": "BAD_REQUEST", "details": "Corredor no soportado"},
        )

        with (
            patch.object(api_client, "_session", session),
            self.assertRaises(api_client.APIError) as ctx,
        ):
            api_client.send_chat_message("hola", {})

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Corredor no soportado", str(ctx.exception))

    def test_send_chat_message_raises_api_error_on_422(self):
        session = MagicMock()
        session.post.return_value = _response(
            422, {"error": "missing_data", "code": "UNPROCESSABLE", "details": "Falta amount_eur"}
        )

        with (
            patch.object(api_client, "_session", session),
            self.assertRaises(api_client.APIError) as ctx,
        ):
            api_client.send_chat_message("hola", {})

        self.assertEqual(ctx.exception.status_code, 422)

    def test_rate_limit_error_is_reported(self):
        session = MagicMock()
        session.post.return_value = _response(
            429,
            {
                "error": "rate_limited",
                "code": "TOO_MANY_REQUESTS",
                "details": "Demasiadas peticiones.",
            },
        )

        with (
            patch.object(api_client, "_session", session),
            self.assertRaises(api_client.APIError) as ctx,
        ):
            api_client.send_chat_message("hola", {})

        self.assertEqual(ctx.exception.status_code, 429)

    def test_connection_error_is_retried_and_raises(self):
        session = MagicMock()
        session.post.side_effect = requests.exceptions.ConnectionError("offline")

        with (
            patch.object(api_client, "_session", session),
            patch.object(api_client.time, "sleep"),
            self.assertRaises(api_client.APIError) as ctx,
        ):
            api_client.send_chat_message("hola", {})

        self.assertEqual(ctx.exception.error_data.get("code"), "CONNECTION_ERROR")
        self.assertEqual(session.post.call_count, api_client.MAX_RETRIES + 1)

    def test_check_api_health_true(self):
        session = MagicMock()
        session.get.return_value = _response(200, {"status": "ok"})
        with patch.object(api_client, "_session", session):
            self.assertTrue(api_client.check_api_health())

    def test_check_api_health_false_on_error(self):
        session = MagicMock()
        session.get.side_effect = requests.exceptions.RequestException("offline")
        with patch.object(api_client, "_session", session):
            self.assertFalse(api_client.check_api_health())


class TestDemoData(unittest.TestCase):
    def test_demo_preview_is_honest_and_consistent(self):
        data = get_demo_response(amount_eur=10000, fee_eur=40, scenario_drop_pct=3)
        agent = data["agent"]

        self.assertTrue(data["reply"])
        self.assertEqual(agent["execution_mode"], "frontend_demo")
        self.assertTrue(agent["degraded"])
        self.assertEqual(agent["tools_used"], [])
        self.assertEqual(agent["calculation_source"], "frontend_preview")

        scenarios = agent["scenarios"]
        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0]["amount_received"], 1444200)
        self.assertEqual(scenarios[1]["amount_received"], 1400874)
        self.assertEqual(agent["difference"]["amount"], 43326)
        self.assertTrue(agent["alerts"])


if __name__ == "__main__":
    unittest.main()
