import asyncio
import json
import subprocess
import time
from swarm.tools.adapters.api_mcp import ApiMcpAdapter
from swarm.tools.effects import InMemoryEffectStore
from swarm.tools.v17_gateway import ConsequentialToolGateway

async def probe(name, transport, post_failure=False, timeout=1):
    adapter = ApiMcpAdapter(transport=transport)
    if post_failure:
        def fail_post(*args):
            raise RuntimeError('synthetic_post_failure')
        adapter.observe_post_state = fail_post
    store = InMemoryEffectStore()
    gateway = ConsequentialToolGateway(adapter, project_id='synthetic_debug',
        allowed_scopes={'network.https','mcp.call'}, current_lease_generation=1, store=store)
    env=adapter.normalize({'project_id':'synthetic_debug','body':'synthetic only'})
    env.timeout_seconds=timeout
    env.approval_id=gateway.make_approval(env).approval_id
    start=time.monotonic()
    try:
        receipt=await gateway.execute_envelope(env)
        result={'receipt_outcome':receipt.outcome}
    except Exception as exc:
        result={'raised':type(exc).__name__}
    row=store.get(project_id=env.project_id,effect_key=env.effect_key)
    print(json.dumps({'case':name,'elapsed_seconds':round(time.monotonic()-start,3),
        'state':row['state'] if row else None,'reason':row.get('state_reason') if row else None,
        'adapter_calls':adapter.call_count,**result}),flush=True)

def boom(*args): raise RuntimeError('synthetic ambiguous transport failure')
def slow(*args):
    time.sleep(1.2)
    return {'outcome':'succeeded'}
async def main():
    print('source_sha='+subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    await probe('empty_outcome',lambda *args:{})
    await probe('unrecognized_outcome',lambda *args:{'outcome':'arbitrary'})
    await probe('ambiguous_exception',boom)
    await probe('deadline_1s',slow)
    await probe('post_observation_failure',lambda *args:{'outcome':'succeeded'},post_failure=True)
    adapter=ApiMcpAdapter()
    gateway=ConsequentialToolGateway(adapter,project_id='synthetic_debug',allowed_scopes=set(),current_lease_generation=1)
    print(json.dumps({'case':'omitted_store','accepted':True,'store_type':type(gateway.store).__name__}))
    env=adapter.normalize({'project_id':'synthetic_debug'})
    print(json.dumps({'case':'unobservable_echo_reconcile','result':adapter.reconcile(env,[])}))
asyncio.run(main())
