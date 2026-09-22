"""Unit regressions for the V1.7-only owner directive, not product live proof."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from execution_guard import evaluate, scope_denial


CONTROL = {'goal_version': '1.7', 'allowed_phases': ['v17']}


def documents(status='ready'):
    return {
        'v17': {'packets': [{'id': 'R1', 'type': 'code', 'status': status}]},
        'v23': {'packets': [{'id': '18-01', 'type': 'code', 'status': 'ready'}]},
        'v30': {'v30_packets': [{'id': 'V30A-001', 'type': 'code', 'status': 'ready'}]},
    }


class ScopeTests(unittest.TestCase):
    def test_v17_work_remains_available(self):
        self.assertEqual(evaluate(documents(), CONTROL)['ready'], ['R1'])

    def test_v18_to_v23_phase_rejected_even_if_ready(self):
        result = evaluate(documents(), CONTROL, 'v23')
        self.assertFalse(result['ok'])
        self.assertEqual(result['errors'], ['scope_forbidden:v23'])
        self.assertEqual(result['ready'], [])

    def test_v30_phase_rejected_even_if_ready(self):
        result = evaluate(documents(), CONTROL, 'v30')
        self.assertFalse(result['ok'])
        self.assertEqual(result['ready'], [])
        self.assertEqual(result['preflight_only'], [])

    def test_completion_does_not_unlock_future_phase(self):
        data = documents('live_checkpointed')
        self.assertEqual(evaluate(data, CONTROL)['ready'], [])
        self.assertFalse(evaluate(data, CONTROL, 'v23')['ok'])

    def test_malformed_scope_fails_closed(self):
        for allowed in (None, [], 'v17', ['unknown'], [1], {}):
            with self.subTest(allowed=allowed):
                result = scope_denial({'allowed_phases': allowed}, 'v17')
                self.assertEqual(result['errors'], ['invalid_allowed_phases'])

    def test_goal_ceiling_cannot_be_broadened_by_phase_list(self):
        result = scope_denial({'goal_version': '1.7', 'allowed_phases': ['v17', 'v23']}, 'v23')
        self.assertEqual(result['errors'], ['scope_ceiling_conflict:goal_version=1.7'])

    def test_legacy_control_without_scope_fields_is_compatible(self):
        self.assertEqual(evaluate(documents(), {}, 'v23')['ready'], ['18-01'])

    def test_does_not_mutate_control_or_queue_status(self):
        data, policy = documents(), copy.deepcopy(CONTROL)
        before = copy.deepcopy((data, policy))
        evaluate(data, policy, 'v23')
        self.assertEqual((data, policy), before)

    def test_existing_independent_review_hold_is_preserved(self):
        data = documents()
        data['v17']['packets'].append({'id': 'R2', 'type': 'code', 'status': 'impl_complete'})
        policy = {**CONTROL, 'review_before': {'R1': ['R2']}}
        self.assertNotIn('R1', evaluate(data, policy)['ready'])

    def test_live_dependency_review_pending_is_not_a_pass(self):
        data = documents()
        data['v17']['packets'] = [
            {'id': 'R1', 'type': 'code', 'status': 'review_pending', 'audit': 'submitted'},
            {'id': 'CP', 'type': 'live', 'status': 'planned', 'depends': ['R1']},
        ]
        self.assertNotIn('CP', evaluate(data, CONTROL)['ready'])

    def _run_cli(self, phase, include_queue):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            policy = {**CONTROL, 'heartbeat_path': 'absent.json'}
            (root / 'EXECUTION_CONTROL.json').write_text(json.dumps(policy))
            if include_queue:
                (root / 'V17_RECOVERY_PACKET_QUEUE.json').write_text(
                    json.dumps(documents()['v17'])
                )
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('execution_guard.py')),
                 '--coord', folder, '--phase', phase, '--json'],
                check=False, capture_output=True, text=True, timeout=10,
            )
            return result.returncode, json.loads(result.stdout)

    def test_cli_v17_does_not_require_future_queue_files(self):
        code, result = self._run_cli('v17', include_queue=True)
        self.assertEqual(code, 0)
        self.assertEqual(result['ready'], ['R1'])
        self.assertEqual(result['packet_count'], 1)

    def test_cli_forbidden_phase_rejected_before_any_queue_read(self):
        code, result = self._run_cli('v23', include_queue=False)
        self.assertEqual(code, 1)
        self.assertEqual(result['errors'], ['scope_forbidden:v23'])


if __name__ == '__main__':
    unittest.main()
