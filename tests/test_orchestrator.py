import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.src.agent import orchestrator


def _tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _message(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


class FakeCompletions:
    """Simula las respuestas del LLM en dos rondas: tool call y respuesta final."""

    def __init__(self, tool_calls, final_content):
        self.tool_calls = tool_calls
        self.final_content = final_content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return SimpleNamespace(
                choices=[SimpleNamespace(message=_message(tool_calls=self.tool_calls))]
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=_message(content=self.final_content))]
        )


class FakeClient:
    def __init__(self, tool_calls, final_content):
        self.chat = SimpleNamespace(completions=FakeCompletions(tool_calls, final_content))


@patch.dict(os.environ, {"FX_SOURCE": "demo"})
class TestOrchestrator(unittest.TestCase):
    """Comprueba el bucle de tool calling sin llamar al LLM real."""

    def test_agent_executes_both_tools_and_integrates(self):
        tool_calls = [
            _tool_call("call_1", "get_fx_reference", {"base": "EUR", "quote": "KES"}),
            _tool_call(
                "call_2",
                "calculate_transfer_scenarios",
                {
                    "amount_eur": 10000,
                    "rate": 145.0,
                    "fee_eur": 40,
                    "currency": "KES",
                    "variations": [-3],
                },
            ),
        ]
        client = FakeClient(tool_calls, "El socio local recibiría 1.444.200 KES.")

        with patch.object(orchestrator, "_get_llm_client", return_value=client):
            result = orchestrator.run_agent(
                "Quiero enviar 10000 EUR a Kenia",
                {
                    "amount_eur": 10000,
                    "destination_country": "KE",
                    "currency": "KES",
                    "fee_eur": 40,
                    "scenario_drop_pct": 3,
                },
            )

        agent = result["agent"]
        self.assertEqual(agent["tools_used"], ["get_fx_reference", "calculate_transfer_scenarios"])
        self.assertEqual(len(agent["scenarios"]), 2)
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)
        self.assertEqual(agent["scenarios"][1]["amount_received"], 1400874)
        self.assertEqual(agent["difference"]["amount"], 43326)
        self.assertEqual(agent["execution_mode"], "llm_tools")
        self.assertFalse(agent["degraded"])
        self.assertEqual(agent["calculation_source"], "financial_engine")
        self.assertTrue(any("Tasa de referencia 145.0" in a for a in agent.get("assumptions", [])))
        self.assertIn("KES", result["reply"])

    def test_llm_cannot_override_financial_parameters(self):
        # LLM intenta manipular importe, tasa, moneda y variación; el backend debe usar contexto/tasa verificada
        tool_calls = [
            _tool_call("call_1", "get_fx_reference", {"base": "USD", "quote": "GHS"}),
            _tool_call(
                "call_2",
                "calculate_transfer_scenarios",
                {
                    "amount_eur": 1,
                    "rate": 9999,
                    "fee_eur": 0,
                    "currency": "USD",
                    "variations": [-50],
                },
            ),
        ]
        client = FakeClient(tool_calls, "Respuesta del modelo.")
        context = {
            "amount_eur": 10000,
            "destination_country": "KE",
            "currency": "KES",
            "fee_eur": 40,
            "scenario_drop_pct": 3,
        }
        with patch.object(orchestrator, "_get_llm_client", return_value=client):
            result = orchestrator.run_agent("Manipula los datos", context)

        agent = result["agent"]
        self.assertEqual(agent["execution_mode"], "llm_tools")
        self.assertFalse(agent["degraded"])
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)
        self.assertEqual(agent["scenarios"][1]["amount_received"], 1400874)
        self.assertEqual(agent["difference"]["amount"], 43326)
        self.assertEqual(agent["scenarios"][0]["currency"], "KES")

    def test_reply_without_tools_uses_honest_fallback_when_context_allows(self):
        client = FakeClient([], "Te explico sin usar herramientas.")
        context = {
            "amount_eur": 10000,
            "destination_country": "KE",
            "currency": "KES",
            "fee_eur": 40,
            "scenario_drop_pct": 3,
        }
        with patch.object(orchestrator, "_get_llm_client", return_value=client):
            result = orchestrator.run_agent("Dime el resultado sin calcular", context)

        agent = result["agent"]
        self.assertEqual(agent["execution_mode"], "deterministic_fallback")
        self.assertTrue(agent["degraded"])
        self.assertEqual(agent["tools_used"], [])
        self.assertEqual(agent["calculation_source"], "demo_scenarios")
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)
        self.assertEqual(agent["difference"]["amount"], 43326)

    def test_tool_error_does_not_expose_unverified_scenarios(self):
        # FX falla -> cálculo no verificable -> fallback determinista honesto (mismo contexto B1)
        def fake_run_tool(name, arguments):
            if name == "get_fx_reference":
                return {"error": "fx unavailable"}
            return {"scenarios": [], "difference": {}}

        client = FakeClient([_tool_call("call_1", "get_fx_reference", {"base": "EUR", "quote": "KES"})], "Fin")
        context = {
            "amount_eur": 10000,
            "destination_country": "KE",
            "currency": "KES",
            "fee_eur": 40,
            "scenario_drop_pct": 3,
        }
        with patch.object(orchestrator, "_get_llm_client", return_value=client), \
             patch.object(orchestrator, "_run_tool", side_effect=fake_run_tool):
            result = orchestrator.run_agent("Simula", context)

        agent = result["agent"]
        self.assertEqual(agent["execution_mode"], "deterministic_fallback")
        self.assertTrue(agent["degraded"])
        self.assertEqual(agent["tools_used"], [])
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)

    def test_max_rounds_exhausted_returns_honest_fallback(self):
        tool_calls = [_tool_call("call_loop", "get_fx_reference", {"base": "EUR", "quote": "KES"})]
        client = FakeClient(tool_calls, "nunca llega")
        context = {
            "amount_eur": 10000,
            "destination_country": "KE",
            "currency": "KES",
            "fee_eur": 40,
            "scenario_drop_pct": 3,
        }
        with patch.object(orchestrator, "_get_llm_client", return_value=client), \
             patch.object(orchestrator, "MAX_ROUNDS", 1):
            result = orchestrator.run_agent("Simula", context)

        agent = result["agent"]
        self.assertEqual(agent["execution_mode"], "deterministic_fallback")
        self.assertTrue(agent["degraded"])
        self.assertEqual(agent["tools_used"], [])
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)
        self.assertEqual(agent["difference"]["amount"], 43326)

    def test_fallback_when_llm_unavailable(self):
        with patch.object(
            orchestrator, "_get_llm_client", side_effect=RuntimeError("sin clave")
        ):
            result = orchestrator.run_agent(
                "Quiero enviar 10000 EUR a Kenia",
                {
                    "amount_eur": 10000,
                    "destination_country": "KE",
                    "currency": "KES",
                    "fee_eur": 40,
                    "scenario_drop_pct": 3,
                },
            )

        agent = result["agent"]
        self.assertEqual(agent["execution_mode"], "deterministic_fallback")
        self.assertTrue(agent["degraded"])
        self.assertEqual(agent["tools_used"], [])
        self.assertIn("fallback", agent["reasoning_summary"].lower())
        self.assertEqual(agent["scenarios"][0]["amount_received"], 1444200)
        self.assertEqual(agent["scenarios"][1]["amount_received"], 1400874)
        self.assertEqual(agent["difference"]["amount"], 43326)


if __name__ == "__main__":
    unittest.main()
