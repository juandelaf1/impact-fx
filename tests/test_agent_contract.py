import copy
import os
import unittest
from unittest.mock import patch

from backend.src.agent import orchestrator as o
from test_orchestrator import FakeClient, _tool_call

CONTEXT = {'amount_eur': 10000, 'fee_eur': 40, 'currency': 'KES',
           'destination_country': 'KE', 'scenario_drop_pct': 3}
FX = {'rate': 145.0, 'source': 'frankfurter', 'date': '2026-11-12', 'is_mock': False}


def run(names, context=None, runner=None):
    client = FakeClient([_tool_call(str(i), name, {}) for i, name in enumerate(names)], 'Respuesta de prueba.')
    with patch.object(o, '_get_llm_client', return_value=client):
        if runner is None:
            return o.run_agent('Simula', CONTEXT if context is None else context)
        with patch.object(o, '_run_tool', side_effect=runner):
            return o.run_agent('Simula', CONTEXT if context is None else context)


@patch.dict(os.environ, {'FX_SOURCE': 'demo'})
class TestAgentContract(unittest.TestCase):
    def assert_contract(self, response, fallback, degraded):
        agent = response['agent']
        for key in ('fx_reference', 'is_fallback', 'scenarios', 'difference',
                    'execution_mode', 'degraded', 'fx_source', 'calculation_source'):
            self.assertIn(key, agent)
        self.assertIs(agent['is_fallback'], fallback)
        self.assertIs(agent['degraded'], degraded)
        if fallback:
            self.assertIsNone(agent['fx_reference'])
            self.assertEqual(agent['tools_used'], [])
        if agent['fx_reference'] is not None:
            self.assertEqual(set(agent['fx_reference']), {'rate', 'source', 'date', 'is_mock'})
        return agent

    def test_normal_has_valid_fx_and_budget(self):
        agent = self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios']), False, False)
        self.assertEqual(agent['fx_reference']['source'], 'demo_reference')
        self.assertEqual(agent['budget_impact']['budget_gap'], 43326)
        self.assertTrue(agent['budget_impact']['is_synthetic_demo'])

    def test_degraded_without_fx_has_no_invented_source(self):
        agent = self.assert_contract(run([], {}), False, True)
        self.assertIsNone(agent['fx_reference'])
        self.assertIsNone(agent['fx_source'])
        self.assertEqual(agent['scenarios'], [])
        self.assertEqual(agent['difference'], {})
        self.assertNotIn('budget_impact', agent)

    def test_degraded_can_keep_a_valid_fx_without_calculation(self):
        agent = self.assert_contract(run(['get_fx_reference'], {'currency': 'KES'}), False, True)
        self.assertEqual(agent['fx_reference']['rate'], 145)
        self.assertEqual(agent['scenarios'], [])
        self.assertNotIn('budget_impact', agent)

    def test_fallback_with_and_without_scenarios(self):
        for context, has_scenarios in [(CONTEXT, True), ({}, False),
                                       ({**CONTEXT, 'scenario_drop_pct': 'bad'}, False)]:
            with self.subTest(context=context):
                agent = self.assert_contract(o._fallback_response(context), True, True)
                self.assertEqual(bool(agent['scenarios']), has_scenarios)
                self.assertEqual('budget_impact' in agent, has_scenarios)
                if has_scenarios:
                    self.assertEqual(agent['budget_impact']['budget_gap'], 43326)

    def test_all_fallback_entrypoints_reset_fx(self):
        responses = [run([]), run(['get_fx_reference'])]
        with patch.object(o, '_get_llm_client', side_effect=RuntimeError('offline')):
            responses.append(o.run_agent('Simula', CONTEXT))
        with patch.object(o, 'MAX_ROUNDS', 1):
            responses.append(run(['get_fx_reference', 'calculate_transfer_scenarios']))
        for result in responses:
            self.assert_contract(result, True, True)

    def test_incomplete_invalid_and_error_fx_are_rejected(self):
        invalid = [None, [], {}, {**FX, 'error': 'failed'}]
        invalid += [{k: v for k, v in FX.items() if k != field} for field in FX]
        invalid += [{**FX, 'rate': value} for value in (True, 0, -1, float('nan'), float('inf'), '145')]
        invalid += [{**FX, 'date': '2026-02-30'}, {**FX, 'is_mock': 'false'}, {**FX, 'source': ''}]
        for value in invalid:
            with self.subTest(value=value):
                agent = self.assert_contract(run(['get_fx_reference'], {'currency': 'KES'}, lambda *_: value), False, True)
                self.assertIsNone(agent['fx_reference'])
                self.assertNotIn('get_fx_reference', agent['tools_used'])

    def test_new_fx_invalidates_old_calculation(self):
        for second in ({**FX, 'rate': 150}, {'error': 'offline'}, None):
            count = 0
            def runner(name, arguments):
                nonlocal count
                if name == 'get_fx_reference':
                    count += 1
                    return FX if count == 1 else second
                return o.calculate_transfer_scenarios(**arguments)
            with self.subTest(second=second):
                agent = self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios', 'get_fx_reference'], runner=runner), True, True)
                self.assertEqual(agent['calculation_source'], 'demo_scenarios')

    def test_invalid_or_forged_calculation_is_not_exposed(self):
        for invalid in (None, {}, {'scenarios': [{}, {}], 'difference': {}}, {'error': 'failed'}):
            def runner(name, arguments):
                return FX if name == 'get_fx_reference' else invalid
            with self.subTest(invalid=invalid):
                self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios'], runner=runner), True, True)

    def test_later_invalid_calculation_clears_previous_success(self):
        count = 0
        def runner(name, arguments):
            nonlocal count
            if name == 'get_fx_reference':
                return FX
            count += 1
            return o.calculate_transfer_scenarios(**arguments) if count == 1 else {}
        self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios', 'calculate_transfer_scenarios'], runner=runner), True, True)

    def test_corrupt_fallback_fixture_is_not_exposed(self):
        fixture = copy.deepcopy(o.find_demo_scenario(10000, 'KES', -3, 40))
        fixture['expected']['difference']['amount'] = 999999
        with patch.object(o, 'find_demo_scenario', return_value=fixture):
            agent = self.assert_contract(o._fallback_response(CONTEXT), True, True)
        self.assertEqual(agent['scenarios'], [])
        self.assertNotIn('budget_impact', agent)

    def test_zero_drop_remains_zero(self):
        agent = self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios'], {**CONTEXT, 'scenario_drop_pct': 0}), False, False)
        self.assertEqual(agent['difference']['amount'], 0)
        self.assertEqual(agent['budget_impact']['budget_gap'], 0)

    def test_live_source_is_not_llm_provider(self):
        def runner(name, arguments):
            return FX if name == 'get_fx_reference' else o.calculate_transfer_scenarios(**arguments)
        agent = self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios'], runner=runner), False, False)
        self.assertEqual(agent['fx_source'], 'frankfurter')
        self.assertEqual(agent['fx_reference'], FX)

    def test_project_budget_request_is_not_applied_to_demo_budget_impact(self):
        ctx = {**CONTEXT, 'project_budget': [{'name': 'Custom', 'amount_local': 1}]}
        agent = self.assert_contract(run(['get_fx_reference', 'calculate_transfer_scenarios'], ctx), False, False)
        self.assertIn('budget_impact', agent)
        self.assertTrue(agent['budget_impact']['is_synthetic_demo'])
        self.assertTrue(any('context.project_budget recibido pero no aplicado' in a for a in agent.get('assumptions', [])))

        fb = self.assert_contract(o._fallback_response(ctx), True, True)
        self.assertIn('budget_impact', fb)
        self.assertTrue(any('context.project_budget recibido pero no aplicado' in a for a in fb.get('assumptions', [])))
