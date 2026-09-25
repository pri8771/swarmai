"""Read-only source review: exercise isolated temporary state, no real services."""
import os
import sys
import json
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).parent / 'cursor-review-180eb73a'
for key in list(os.environ):
    if key.startswith('SWARM_'):
        del os.environ[key]
sys.path.insert(0, str(SOURCE / 'src'))
results = {'source_sha': '180eb73a4b67103b3e38f4aaa550ac444307d60a'}
with TemporaryDirectory(prefix='swarm-review-') as temp:
    root = Path(temp)
    os.environ['SWARM_REPO_ROOT'] = str(root / 'bootstrap')
    from fastapi.testclient import TestClient
    from swarm.api.app import create_app
    from swarm.contracts.fixtures import sample_mission
    from swarm.workspace.artifacts import ArtifactStore
    from swarm.evals.dataset import load_dataset
    from swarm.evals.graders import grade_case
    from swarm.evals.synthetic_harness import LiveGrant, run_synthetic_harness
    from swarm.runtime.adapters.native import NativeRuntimeAdapter
    from swarm.tools.sandbox_runner import IsolatedCodeRunner

    def app_for(path):
        return create_app(repo_root=path, seed_loopback_token='review-only-token',
                          install_project_id='proj_review', db_reachable=False)
    headers = {'Authorization': 'Bearer review-only-token'}
    app = app_for(root / 'server')
    client = TestClient(app)
    mission = sample_mission().model_copy(update={'id': 'msn_review', 'project_id': 'proj_review'})
    body = {'mission': mission.model_dump(mode='json'), 'task_family': 'extract',
            'required_checks': {'count': 99}}
    created = client.post('/v1/missions', headers=headers, json=body)
    assert created.status_code == 200, created.text
    review = client.post('/v1/missions/msn_review/review', headers=headers,
                         json={'produced': {'checks': {'count': 1}}, 'required_checks': {'count': 1}})
    results['acceptance_without_execution'] = {
        'http_status': review.status_code,
        'accepted': review.json().get('accepted'),
        'mission_status': review.json().get('mission', {}).get('status'),
        'original_required_count': 99, 'submitted_count': 1,
        'workers_enrolled': len(app.state.store.workers._workers),
        'produced_artifact': False,
    }
    enrollment = client.post('/v1/workers/enroll', headers=headers, json={'project_id': 'proj_review'})
    assert enrollment.status_code == 200, enrollment.text
    enrolled = enrollment.json()
    before = len(client.get('/v1/workers', headers=headers).json()['workers'])
    replay_headers = {**headers, 'Idempotency-Key': 'artifact-review-replay'}
    payload = {'kind': 'result', 'content_text': 'review payload'}
    first_artifact = client.post('/v1/missions/msn_review/artifacts', headers=replay_headers, json=payload)
    assert first_artifact.status_code == 200, first_artifact.text
    first_id = first_artifact.json()['artifact']['artifact_id']
    second_app = app_for(root / 'server')
    cold = TestClient(second_app)
    heartbeat = cold.post('/v1/workers/heartbeat', headers=headers, json={
        'worker_id': enrolled['worker']['worker_id'],
        'generation': enrolled['worker']['lease_generation'],
        'token': enrolled['membership_token'],
    })
    results['worker_restart'] = {
        'workers_before': before,
        'workers_after': len(cold.get('/v1/workers', headers=headers).json()['workers']),
        'heartbeat_after_restart_status': heartbeat.status_code,
    }
    replay = cold.post('/v1/missions/msn_review/artifacts', headers=replay_headers, json=payload)
    results['artifact_idempotency_after_restart'] = {
        'http_status': replay.status_code,
        'same_id': first_id == replay.json()['artifact']['artifact_id'],
        'original_artifact_read_status': cold.get(
            f'/v1/missions/msn_review/artifacts/{first_id}/content', headers=headers).status_code,
    }
    second_id = replay.json()['artifact']['artifact_id']
    second_app.state.store.artifact_store().delete(second_id)
    results['deleted_artifact_read'] = {
        'http_status': cold.get(
            f'/v1/missions/msn_review/artifacts/{second_id}/content', headers=headers).status_code,
    }
    a = ArtifactStore(root / 'shared-cas')
    b = ArtifactStore(root / 'shared-cas')
    refa = a.put(b'A', media_type='text/plain', owner_scope='p')
    refb = b.put(b'B', media_type='text/plain', owner_scope='p')
    reloaded = ArtifactStore(root / 'shared-cas')
    results['artifact_multiple_writers'] = {
        'metadata_ids_written': 2, 'metadata_ids_after_reload': len(reloaded._meta),
        'first_reference_preserved': refa.id in reloaded._meta,
        'second_reference_preserved': refb.id in reloaded._meta,
    }
    cases = load_dataset(SOURCE / 'benchmarks/starter.jsonl')
    case = next(c for c in cases if c.grader['kind'] == 'python_unit')
    grade = grade_case(case, 'print(\'{"ok": true}\')\nraise SystemExit(0)\n')
    results['grader_forged_stdout'] = {
        'case_id': case.id, 'correct': grade.correct, 'detail': grade.detail,
        'solution_function_defined': False,
    }
    marker = root / 'outside-sandbox-marker.txt'
    marker.write_text('review-only-marker')
    sandbox = root / 'sandbox'
    sandbox.mkdir()
    (sandbox / 'probe.py').write_text(
        'from pathlib import Path\nprint(Path(' + repr(str(marker)) + ').read_text())\n')
    sandbox_result = IsolatedCodeRunner(sandbox, network=False).run_python('probe.py')
    results['sandbox_scope'] = {
        'read_synthetic_file_outside_work_dir': sandbox_result.stdout.strip() == 'review-only-marker',
        'real_user_files_accessed': False,
    }
    try:
        LiveGrant('review', ('verified_free_route',), 0.0, 'zero-spend-eval', True).assert_usable()
        zero = 'accepted'
    except Exception as exc:
        zero = str(exc)
    results['zero_spend_grant'] = zero
    report = run_synthetic_harness(dataset_path=SOURCE / 'benchmarks/starter.jsonl', max_cases=1)
    saved = report.to_dict()
    claimed_hash = saved['report_hash']
    saved['report_hash'] = None
    recomputed = hashlib.sha256(json.dumps(saved, sort_keys=True, default=str).encode()).hexdigest()
    results['report_hash_verification'] = {'matches_canonical_payload': recomputed == claimed_hash}
    qualification = NativeRuntimeAdapter().qualify()
    results['native_admission'] = {
        'availability': qualification.availability.value,
        'kernel_mediation_proven': qualification.kernel_mediation_proven,
        'unproven': [c.capability for c in qualification.capabilities if c.status.value == 'unproven'],
    }
    planroot = SOURCE / 'docs/swarm-mvp'
    manifest = json.loads((planroot / 'PLAN_MANIFEST.json').read_text())
    results['plan_manifest_hashes'] = {
        entry['path']: hashlib.sha256((planroot / entry['path']).read_bytes()).hexdigest() == entry['sha256']
        for entry in manifest['files']
    }
print(json.dumps(results, indent=2))
