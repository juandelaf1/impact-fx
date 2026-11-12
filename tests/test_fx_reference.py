import io
import json
import os
import unittest
from contextlib import nullcontext
from http.client import IncompleteRead
from urllib.error import HTTPError, URLError
from types import SimpleNamespace
from unittest.mock import patch

from backend.src.tools.get_fx_reference import get_fx_reference
from backend.src.agent import orchestrator
from test_orchestrator import FakeClient, _tool_call

TARGET = 'backend.src.tools.get_fx_reference.urlopen'
PAYLOAD = {'base': 'EUR', 'quote': 'KES', 'rate': 144.76, 'date': '2026-11-11'}


def response(payload):
    return io.StringIO(json.dumps(payload))


@patch.dict(os.environ, {'FX_SOURCE': 'live'})
class TestFxReference(unittest.TestCase):
    def test_live_success_and_normalization(self):
        with patch(TARGET, return_value=response(PAYLOAD)) as request:
            result = get_fx_reference(' eur ', ' kes ')
        request.assert_called_once_with('https://api.frankfurter.dev/v2/rate/EUR/KES', timeout=8)
        self.assertEqual(result, {'rate': 144.76, 'source': 'frankfurter',
                                 'date': '2026-11-11', 'is_mock': False})

    def test_demo_and_default_do_not_use_network(self):
        for source in (None, 'demo', ' DEMO '):
            with self.subTest(source=source), patch.dict(os.environ), patch(TARGET) as request:
                if source is None:
                    os.environ.pop('FX_SOURCE', None)
                else:
                    os.environ['FX_SOURCE'] = source
                result = get_fx_reference('EUR', 'KES')
                self.assertEqual(result['rate'], 145)
                self.assertTrue(result['is_mock'])
                request.assert_not_called()

    def test_historical_lookup_remains_local(self):
        with patch(TARGET) as request:
            result = get_fx_reference('EUR', 'KES', '2026-11-12')
            self.assertTrue(result['is_mock'])
            with self.assertRaises(ValueError):
                get_fx_reference('EUR', 'KES', '1900-01-01')
            request.assert_not_called()

    def test_transport_failures_fall_back(self):
        errors = [URLError('offline'), TimeoutError('timeout'),
                  HTTPError('https://api.frankfurter.dev', 503, 'unavailable', {}, None),
                  ConnectionResetError('reset'), IncompleteRead(b'partial')]
        for error in errors:
            with self.subTest(error=type(error).__name__), patch(TARGET, side_effect=error):
                with self.assertWarnsRegex(RuntimeWarning, 'datos ficticios'):
                    result = get_fx_reference('EUR', 'KES')
                self.assertEqual(result['rate'], 145)
                self.assertEqual(result['source'], 'demo_reference')
                self.assertEqual(result['date'], '2026-11-12')
                self.assertTrue(result['is_mock'])

    def test_malformed_responses_fall_back(self):
        payloads = [None, [], {}, {**PAYLOAD, 'quote': 'USD'}, {**PAYLOAD, 'base': 'USD'}]
        for value in (0, -1, float('nan'), float('inf'), True, None, [], 'bad', 10**400):
            payloads.append({**PAYLOAD, 'rate': value})
        for value in (None, '', '2026-02-30', '20261111', 123):
            payloads.append({**PAYLOAD, 'date': value})
        for field in ('rate', 'date', 'base', 'quote'):
            payloads.append({k: v for k, v in PAYLOAD.items() if k != field})
        for payload in payloads:
            with self.subTest(payload=payload), patch(TARGET, return_value=response(payload)):
                with self.assertWarns(RuntimeWarning):
                    self.assertTrue(get_fx_reference('EUR', 'KES')['is_mock'])
        for body in (b'not json', b'\xff'):
            with self.subTest(body=body), patch(TARGET, return_value=io.BytesIO(body)):
                with self.assertWarns(RuntimeWarning):
                    self.assertTrue(get_fx_reference('EUR', 'KES')['is_mock'])

    def test_missing_fallback_pair_raises(self):
        with patch(TARGET, side_effect=URLError('offline')):
            with self.assertWarns(RuntimeWarning), self.assertRaisesRegex(ValueError, 'EUR/XXX'):
                get_fx_reference('EUR', 'XXX')

    def test_invalid_inputs_and_configuration_do_not_use_network(self):
        with patch(TARGET) as request:
            for base, quote, date in [(None, 'KES', None), ('', 'KES', None),
                                      ('EUR/x', 'KES', None), ('EUR', '12X', None),
                                      ('EUR', 'KES', 123)]:
                with self.subTest(base=base, quote=quote, date=date), self.assertRaises(ValueError):
                    get_fx_reference(base, quote, date)
            with patch.dict(os.environ, {'FX_SOURCE': 'typo'}), self.assertRaisesRegex(ValueError, 'FX_SOURCE'):
                get_fx_reference('EUR', 'KES')
            request.assert_not_called()

    def test_unexpected_programming_error_is_not_hidden(self):
        with patch(TARGET, side_effect=RuntimeError('bug')), self.assertRaises(RuntimeError):
            get_fx_reference('EUR', 'KES')

    def test_agent_receives_live_and_fallback_metadata(self):
        for live in (True, False):
            with self.subTest(live=live):
                client = FakeClient([_tool_call('fx', 'get_fx_reference',
                                               {'base': 'EUR', 'quote': 'KES'})], 'Referencia obtenida.')
                request = patch(TARGET, return_value=response(PAYLOAD)) if live else patch(TARGET, side_effect=URLError('offline'))
                warning = nullcontext() if live else self.assertWarns(RuntimeWarning)
                with request, warning, patch.object(orchestrator, '_get_llm_client', return_value=client):
                    result = orchestrator.run_agent('Referencia EUR/KES', {})
                messages = client.chat.completions.calls[-1]['messages']
                tool_result = json.loads(next(m['content'] for m in messages if m['role'] == 'tool'))
                self.assertEqual(tool_result['is_mock'], not live)
                self.assertEqual(tool_result['rate'], 144.76 if live else 145)
                self.assertIn('frankfurter' if live else 'demo_reference', result['agent']['assumptions'][0])
                self.assertIn('is_mock=False' if live else 'is_mock=True', result['agent']['assumptions'][0])
                self.assertEqual(result['agent']['tools_used'], ['get_fx_reference'])

    def test_agent_calculates_with_rate_returned_by_live_tool(self):
        client = FakeClient([], 'Listo.')

        def complete(**kwargs):
            results = [m for m in kwargs['messages'] if m['role'] == 'tool']
            if not results:
                calls = [_tool_call('fx', 'get_fx_reference', {'base': 'EUR', 'quote': 'KES'})]
            elif len(results) == 1:
                rate = json.loads(results[0]['content'])['rate']
                calls = [_tool_call('calc', 'calculate_transfer_scenarios', {
                    'amount_eur': 10000, 'fee_eur': 40, 'rate': rate,
                    'currency': 'KES', 'variations': [-3],
                })]
            else:
                calls = []
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content='Simulación completada.' if not calls else None, tool_calls=calls))])

        with patch(TARGET, return_value=response(PAYLOAD)), patch.object(
            orchestrator, '_get_llm_client', return_value=client
        ), patch.object(client.chat.completions, 'create', side_effect=complete):
            result = orchestrator.run_agent('Enviar 10000 EUR a Kenia', {'currency': 'KES'})
        self.assertEqual(result['agent']['scenarios'][0]['amount_received'], 1441809.6)
        self.assertEqual(result['agent']['tools_used'], ['get_fx_reference', 'calculate_transfer_scenarios'])
        self.assertIn('is_mock=False', result['agent']['assumptions'][0])
