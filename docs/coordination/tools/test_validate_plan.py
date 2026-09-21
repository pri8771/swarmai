"""Focused negative tests for readiness and graph safety; no product tests implied."""
import copy
import json
import unittest
from pathlib import Path
import validate_plan as plan

class PlanTests(unittest.TestCase):
    def setUp(self):
        c=Path(__file__).resolve().parents[1]
        self.docs=[json.loads((c/n).read_text()) for n in plan.NAMES]
    def run_plan(self): return plan.validate(*self.docs)
    def packet(self,pid):
        for d in self.docs[:3]:
            for p in d.get('packets',[])+d.get('v30_packets',[]):
                if p['id']==pid: return p
        self.fail(pid)
    def test_baseline_and_ready_set(self):
        r=self.run_plan(); self.assertTrue(r['ok'],r['errors'])
        self.assertEqual(r['ready_v17'],['OPS-CI-01','R27a','R30a','R17a','R02a'])
        self.assertFalse(r['dispatch_authorized'])
    def test_unresolved_dependency(self):
        self.packet('R27a')['depends']=['missing']
        self.assertFalse(self.run_plan()['ok'])
    def test_duplicate_id(self):
        self.docs[0]['packets'].append(copy.deepcopy(self.packet('R27a')))
        self.assertFalse(self.run_plan()['ok'])
    def test_split_cycle_detected_without_recursing_forever(self):
        self.packet('R33c')['split_into']=['R33c']
        self.assertTrue(any('completion cycle' in e for e in self.run_plan()['errors']))
    def test_remediation_back_edge_detected(self):
        self.packet('R27a')['depends']=['R27']
        self.assertTrue(any('completion cycle' in e for e in self.run_plan()['errors']))
    def test_basis_is_provenance_not_completion(self):
        self.assertIn('R27a',self.run_plan()['ready_v17'])
        self.assertEqual(self.packet('R27a')['basis'],['R27'])
    def test_review_hold_blocks_downstream_even_when_source_done(self):
        self.packet('R27c')['status']='impl_complete'
        r=self.run_plan(); self.assertNotIn('R27d',r['ready_v17'])
        self.assertEqual(r['entry_gate_blocked_v17']['R27d'],['REV-R27C'])
    def test_gate_cannot_close_without_evidence(self):
        g=next(x for x in self.docs[0]['gates'] if x['id']=='REV-R27C')
        g['status']='passed'; g['evidence_refs']=[]
        self.assertFalse(self.run_plan()['ok'])
    def test_evidenced_gate_unblocks_specific_dependency(self):
        self.packet('R27c')['status']='impl_complete'
        g=next(x for x in self.docs[0]['gates'] if x['id']=='REV-R27C')
        g.update(status='passed',evidence_refs=['test-only-independent-review'])
        self.assertIn('R27d',self.run_plan()['ready_v17'])
    def test_exit_gate_does_not_block_implementation(self):
        self.packet('R27a')['exit_gates']=['EXT-ACTIONS-BILLING']
        self.assertIn('R27a',self.run_plan()['ready_v17'])
    def test_undefined_gate(self):
        self.packet('R27a')['entry_gates']=['missing']
        self.assertFalse(self.run_plan()['ok'])
    def test_missing_future_contract_field(self):
        self.packet('18-01').pop('negative_tests')
        self.assertFalse(self.run_plan()['ok'])
    def test_future_acceptance_not_worker_state(self):
        self.packet('V30A-001')['status']='accepted'
        self.assertFalse(self.run_plan()['ok'])
    def test_catalog_changes_when_contract_changes(self):
        before=plan.catalog(self.docs[1],self.docs[2])
        self.packet('18-01')['behavior']+=' changed'
        self.assertNotEqual(before,plan.catalog(self.docs[1],self.docs[2]))

if __name__=='__main__': unittest.main()
