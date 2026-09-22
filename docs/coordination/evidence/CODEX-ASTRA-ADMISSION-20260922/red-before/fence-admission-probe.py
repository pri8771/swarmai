from __future__ import annotations
import json, tempfile, threading
from pathlib import Path
from swarm.mission.action_boundary import local_worktree_gateway
from swarm.mission.worker import RepoWorker, WorkerCancellationRequested
from swarm.tools.fences import ActorContext, RevocableFenceProvider

with tempfile.TemporaryDirectory(prefix='swarm-astra-fence-probe-') as d:
    root=Path(d)
    fences=RevocableFenceProvider()
    gateway=local_worktree_gateway(root,fences=fences)
    worker=RepoWorker(root,broker=None,project_id='review_probe',action_gateway=gateway,actor_context=ActorContext(actor='review_probe',project_id='review_probe'),require_broker=False)
    worker._begin_task_effects(mission_id='review_mission',task_id='review_task')
    read_done=threading.Event()
    cancellation_done=threading.Event()
    observations={}
    original_reader=fences.reader
    def pause_reader(**identity):
        read=original_reader(**identity)
        def paused(session):
            captured=read(session)
            observations['captured_generation']=captured['cancellation_generation']
            observations['effect_state_before_cancel']=next(iter(gateway.store.effects.values()))['state']
            read_done.set()
            assert cancellation_done.wait(5)
            observations['current_generation_before_return']=fences.current(**identity).cancellation_generation
            return captured
        return paused
    fences.reader=pause_reader
    def cancel():
        assert read_done.wait(5)
        fences.cancel()
        observations['cancel_returned_while_effect_reserved']=next(iter(gateway.store.effects.values()))['state']=='reserved'
        cancellation_done.set()
    t=threading.Thread(target=cancel)
    t.start()
    try:
        worker._action_effect('fs.write_text',{'path':'late.txt','text':'written after revocation completed'})
    except WorkerCancellationRequested:
        observations['worker_detected_cancel_after_receipt']=True
    t.join(5)
    observations['late_file_exists']=(root/'late.txt').exists()
    observations['receipt_ids']=worker.active_action_receipt_ids
    observations['final_effect_state']=next(iter(gateway.store.effects.values()))['state']
    observations['source']='86f8e0c90e399c683d68ba9628ef48af4723f33f'
    print(json.dumps(observations,indent=2))
