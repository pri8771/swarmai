from __future__ import annotations
import json, os, subprocess, time
from pathlib import Path
import psycopg
from psycopg import sql

repo = Path('/private/tmp/swarm-r28d3-repair-20260922')
out = Path('/tmp/swarm-astra-atomicity-checks-20260922')
env = os.environ.copy()
env['PYTHONPATH'] = f'{repo / "src"}:{repo}'
env['SWARM_ALLOW_PAID'] = 'false'
env['SWARM_LIVE_LOCAL'] = '0'
env.pop('SWARM_DATABASE_URL', None)
results = []

def run(name, argv, use_env=None):
    start=time.monotonic()
    p=subprocess.run(argv,cwd=repo,env=use_env or env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/f'{name}.log').write_text(p.stdout)
    r={'name':name,'argv':argv,'exit_code':p.returncode,'seconds':round(time.monotonic()-start,2),'stdout_file':f'{name}.log'}
    results.append(r)
    (out/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(r),flush=True)
    print(p.stdout[-4000:],flush=True)
    return p

run('identity',['git','rev-parse','HEAD','HEAD^{tree}'])
run('status-before',['git','status','--short'])
run('import-provenance',['uv','run','--no-sync','python','-c','import swarm,sys; print(sys.executable); print(swarm.__file__)'])
run('focused-offline',['uv','run','--no-sync','pytest','tests/mission/test_mission_runtime_async_worker_bridge.py','tests/mission/test_no_auto_promote.py','tests/tools/test_local_admission_guard.py','-q','-rs','--junitxml=/tmp/swarm-astra-atomicity-checks-20260922/focused.xml'])
run('full-offline',['uv','run','--no-sync','pytest','-q','-rs','--tb=short'])
run('ruff-all',['uv','run','--no-sync','ruff','check','.'])
run('mypy',['uv','run','--no-sync','mypy','src/swarm'])
run('diff-check',['git','diff','--check'])

socket='/tmp/swarm-pgcheck.QxqRvZ'
port=56421
db=f'swarm_astra_review_{os.getpid()}_{int(time.time())}'
pg={'socket':socket,'port':port,'database':db,'created':False}
try:
    with psycopg.connect(dbname='postgres',host=socket,port=port,autocommit=True) as c:
        pg['current_user']=c.execute('select current_user').fetchone()[0]
        for k in ['data_directory','port','unix_socket_directories','listen_addresses']:
            pg[k]=c.execute(sql.SQL('SHOW {}').format(sql.Identifier(k))).fetchone()[0]
        assert pg['current_user']=='pchordia' and pg['data_directory']=='/tmp/swarm-pgcheck.QxqRvZ/data' and pg['port']=='56421' and pg['listen_addresses']==''
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db)))
        pg['created']=True
    (out/'postgres.json').write_text(json.dumps(pg,indent=2)+'\n')
    pg_env=env|{'SWARM_DATABASE_URL':f'postgresql+psycopg:///{db}?host={socket}&port={port}'}
    run('full-postgres',['uv','run','--no-sync','pytest','-q','-rs','--tb=short','--junitxml=/tmp/swarm-astra-atomicity-checks-20260922/full-postgres.xml'],pg_env)
    with psycopg.connect(dbname=db,host=socket,port=port,autocommit=True) as c:
        pg['public_tables_after_tests']=c.execute("select count(*) from information_schema.tables where table_schema='public'").fetchone()[0]
finally:
    if pg['created']:
        with psycopg.connect(dbname='postgres',host=socket,port=port,autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db)))
            pg['cleanup_remaining']=c.execute('select count(*) from pg_database where datname=%s',(db,)).fetchone()[0]
    (out/'postgres.json').write_text(json.dumps(pg,indent=2)+'\n')
    print(json.dumps(pg),flush=True)
run('status-after',['git','status','--short'])
