"""Synthetic unit tests for handoff tooling; NOT SwarmAI live/product evidence."""
import copy
import unittest
from datetime import datetime, timezone
from execution_guard import evaluate, heartbeat_assessment


def packet(pid, status='planned', kind='code', depends=(), **extra):
    return dict(id=pid, status=status, type=kind, depends=list(depends), **extra)


def docs(*packets, gates=()):
    return {'v17': {'packets': list(packets), 'gates': list(gates)},
            'v23': {'packets': []}, 'v30': {'v30_packets': []}}


class GuardTests(unittest.TestCase):
    def test_ready_without_dependencies(self):
        self.assertEqual(evaluate(docs(packet('A')), {})['ready'], ['A'])

    def test_ready_label_does_not_override_missing_dependency(self):
        r = evaluate(docs(packet('A', 'ready', depends=['MISSING'])), {})
        self.assertFalse(r['ok']); self.assertEqual(r['ready'], [])

    def test_plain_dependency_cycle(self):
        r = evaluate(docs(packet('A', depends=['B']), packet('B', depends=['A'])), {})
        self.assertFalse(r['ok'])

    def test_split_expansion_cycle(self):
        r = evaluate(docs(packet('P', 'split', split_into=['A']), packet('A', depends=['P'])), {})
        self.assertFalse(r['ok']); self.assertEqual(r['ready'], [])

    def test_empty_split_rejected(self):
        self.assertFalse(evaluate(docs(packet('P', 'split')), {})['ok'])

    def test_repair_can_consume_audited_parent(self):
        r = evaluate(docs(packet('P', 'gaps_found', remediation=['A']), packet('A', depends=['P'])), {})
        self.assertTrue(r['ok']); self.assertEqual(r['ready'], ['A'])

    def test_successor_waits_for_all_repairs(self):
        d = docs(packet('P', 'gaps_found', remediation=['A', 'B']),
                 packet('A', 'impl_complete'), packet('B'), packet('C', depends=['P']))
        self.assertNotIn('C', evaluate(d, {})['ready'])

    def test_completed_repairs_satisfy_successor(self):
        d = docs(packet('P', 'gaps_found', remediation=['A', 'B']),
                 packet('A', 'impl_complete'), packet('B', 'impl_complete'), packet('C', depends=['P']))
        self.assertIn('C', evaluate(d, {})['ready'])

    def test_evidence_only_not_live_checkpoint_dependency(self):
        d = docs(packet('A', 'evidence_only', audit='historical source'), packet('B', kind='live', depends=['A']))
        self.assertNotIn('B', evaluate(d, {})['ready'])

    def test_documented_baseline_can_enable_repair_code(self):
        d = docs(packet('A', 'evidence_only', audit='historical source'), packet('B', depends=['A']))
        self.assertIn('B', evaluate(d, {})['ready'])

    def test_unsubstantiated_evidence_only_not_satisfied(self):
        d = docs(packet('A', 'evidence_only'), packet('B', depends=['A']))
        self.assertNotIn('B', evaluate(d, {})['ready'])

    def test_review_pending_not_live_pass(self):
        d = docs(packet('A', 'review_pending', audit='submitted'), packet('B', kind='live', depends=['A']))
        self.assertNotIn('B', evaluate(d, {})['ready'])

    def test_open_external_gate_blocks_live(self):
        d = docs(packet('A', kind='external_live', gate='G'), gates=[dict(id='G', status='open')])
        self.assertEqual(evaluate(d, {})['ready'], [])

    def test_open_external_gate_does_not_block_harness_code(self):
        d = docs(packet('A', kind='code', gate='G'), gates=[dict(id='G', status='open')])
        self.assertEqual(evaluate(d, {})['ready'], ['A'])

    def test_declared_closed_gate_needs_evidence_reference(self):
        d = docs(packet('A', kind='live', gate='G'), gates=[dict(id='G', status='closed')])
        self.assertEqual(evaluate(d, {})['ready'], [])

    def test_closed_gate_with_evidence_can_run(self):
        d = docs(packet('A', kind='live', gate='G'), gates=[dict(id='G', status='closed', evidence_refs=['receipt'])])
        self.assertEqual(evaluate(d, {})['ready'], ['A'])

    def test_preauthorized_account_requires_local_probe(self):
        d = docs(packet('A', kind='external_live', gate='G'), gates=[dict(id='G', status='preauthorized_if_existing_gh_session_available')])
        r = evaluate(d, {'runtime_probe_gates': ['G']})
        self.assertEqual(r['ready'], []); self.assertEqual(r['preflight_only'][0]['packet'], 'A')

    def test_result_review_gate_does_not_prevent_collecting_evidence(self):
        d = docs(packet('A', kind='live', gate='G'), gates=[dict(id='G', status='open')])
        self.assertEqual(evaluate(d, {'result_only_gates': ['G']})['ready'], ['A'])

    def test_review_hold_enforced(self):
        d = docs(packet('A', 'impl_complete'), packet('B', depends=['A']))
        self.assertNotIn('B', evaluate(d, {'review_before': {'B': ['A']}})['ready'])

    def test_review_reference_and_source_required(self):
        d = docs(packet('A', 'impl_complete'), packet('B', depends=['A']))
        c = {'review_before': {'B': ['A']}, 'reviewed_packets': {'A': {'review_ref': 'review'}}}
        self.assertNotIn('B', evaluate(d, c)['ready'])
        c['reviewed_packets']['A']['source_sha'] = 'source'
        self.assertIn('B', evaluate(d, c)['ready'])

    def test_overlay_closes_real_world_handoff_gap(self):
        d = docs(packet('R34a', 'live_checkpointed'), packet('R33c'),
                 packet('R34b', kind='live', depends=['R34a']))
        c = {'dependency_additions': {'R34b': ['R33c']}}
        self.assertNotIn('R34b', evaluate(d, c)['ready'])
        d['v17']['packets'][1]['status'] = 'live_checkpointed'
        self.assertIn('R34b', evaluate(d, c)['ready'])

    def test_overlay_missing_target_fails_closed(self):
        r = evaluate(docs(packet('A')), {'dependency_additions': {'missing': ['A']}})
        self.assertFalse(r['ok']); self.assertEqual(r['ready'], [])

    def test_lead_decision_not_worker_work(self):
        self.assertEqual(evaluate(docs(packet('A', kind='lead_decision')), {})['ready'], [])

    def test_future_freeze_not_implied_by_authorized_version(self):
        d = docs(); d['v30']['v30_packets'] = [packet('V30A-001', requires_lead_freeze=True)]
        self.assertEqual(evaluate(d, {}, 'v30')['ready'], [])

    def test_other_phases_not_selected(self):
        d = docs(packet('A')); d['v23']['packets'] = [packet('B')]
        self.assertEqual(evaluate(d, {}, 'v17')['ready'], ['A'])
        self.assertEqual(evaluate(d, {}, 'v23')['ready'], ['B'])

    def test_does_not_mutate_input_or_mark_acceptance(self):
        d = docs(packet('A', 'impl_complete'), packet('B'))
        before = copy.deepcopy(d)
        evaluate(d, {'dependency_additions': {'B': ['A']}})
        self.assertEqual(d, before)

    def test_one_active_packet_reported_not_restarted(self):
        r = evaluate(docs(packet('A', 'in_progress')), {})
        self.assertEqual(r['in_progress'], ['A']); self.assertEqual(r['ready'], [])

    def test_undefined_gate_rejected(self):
        self.assertFalse(evaluate(docs(packet('A', gate='bad')), {})['ok'])

    def test_actual_heartbeat_snapshot_is_not_progress(self):
        h = {'last_heartbeat': {'timestamp_utc': '2026-09-21T23:23:56Z',
                               'last_meaningful_activity_at': '2026-09-21T20:05:50Z',
                               'status': 'working', 'current_packet': 'R27'}}
        r = heartbeat_assessment(h, datetime(2026, 9, 21, 23, 24, tzinfo=timezone.utc))
        self.assertEqual(r['state'], 'daemon_alive_activity_stale_verify_process_or_long_job')
        self.assertEqual(r['activity_age_seconds'], 11890)

    def test_future_timestamp_not_fresh(self):
        h = {'timestamp_utc': '2099-01-01T00:00:00Z'}
        self.assertEqual(heartbeat_assessment(h, datetime.now(timezone.utc))['state'], 'unknown_or_invalid_timestamp')

    def test_missing_activity_is_unknown(self):
        n = datetime.now(timezone.utc)
        self.assertEqual(heartbeat_assessment({'timestamp_utc': n.isoformat()}, n)['state'], 'daemon_alive_activity_unknown')


if __name__ == '__main__':
    unittest.main()
