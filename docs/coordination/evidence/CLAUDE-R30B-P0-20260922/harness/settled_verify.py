from __future__ import annotations
import json, os, subprocess, time
from pathlib import Path
import psycopg
from psycopg import sql
PY='/private/tmp/swarm-r28d3-repair-20260922/.venv/bin/python'
repo=Path('/tmp/swarm-astra-r30b-prerequisite-20260922'); out=Path('/tmp/swarm-astra-r30b-p0-resume-20260922/settled')
env=os.environ.copy(); env['PYTHONPATH']=f'{repo/"src"}:{repo}'; env['SWARM_ALLOW_PAID']='false'; env['SWARM_LIVE_LOCAL']='0'; env.pop('SWARM_DATABASE_URL',None)
FILES=['src/swarm/contracts/actions.py','src/swarm/tools/v17_gateway.py','tests/tools/test_gateway_envelope_integrity.py','tests/integration/db/test_execution_attempt_context.py','tests/tools/test_v17_gateway_classification_fences.py']
results=[]
def run(name, argv, use_env=None):
    s=time.monotonic(); p=subprocess.run(argv,cwd=repo,env=use_env or env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/f'{name}.log').write_text(p.stdout)
    r={'name':name,'argv':argv,'exit_code':p.returncode,'seconds':round(time.monotonic()-s,2),'tail':p.stdout.strip().splitlines()[-1:] }
    results.append(r); (out/'checks.json').write_text(json.dumps(results,indent=2)+'\n'); print(json.dumps(r),flush=True); return p
run('identity',['git','rev-parse','HEAD'])
run('blob-hashes',['git','hash-object',*FILES])
run('status-before',['git','status','--short'])
run('import-provenance',[PY,'-c','import swarm,sys; print(sys.executable); print(swarm.__file__)'])
run('diff-check-tracked',['git','diff','--check'])
run('focused-offline',[PY,'-m','pytest','-q','-rs','tests/tools/test_gateway_envelope_integrity.py','tests/integration/db/test_execution_attempt_context.py','tests/tools/test_v17_gateway_classification_fences.py'])
run('full-offline',[PY,'-m','pytest','-q','-rs','--tb=short','-p','no:cacheprovider'])
run('ruff-touched',[PY,'-m','ruff','check',*FILES])
run('ruff-format-touched',[PY,'-m','ruff','format','--check',*FILES])
run('ruff-all',[PY,'-m','ruff','check','.'])
run('mypy',[PY,'-m','mypy','src/swarm'])
socket='/tmp/swarm-pgcheck.QxqRvZ'; port=56421; db=f'swarm_r30b_p0_settled_{os.getpid()}_{int(time.time())}'
pg={'socket':socket,'port':port,'database':db,'created':False}
try:
    with psycopg.connect(dbname='postgres',host=socket,port=port,autocommit=True) as c:
        pg['current_user']=c.execute('select current_user').fetchone()[0]
        for k in ['data_directory','port','listen_addresses']:
            pg[k]=c.execute(sql.SQL('SHOW {}').format(sql.Identifier(k))).fetchone()[0]
        assert pg['current_user']=='pchordia' and pg['data_directory']=='/tmp/swarm-pgcheck.QxqRvZ/data' and pg['port']=='56421' and pg['listen_addresses']==''
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db))); pg['created']=True
    pg_env=env|{'SWARM_DATABASE_URL':f'postgresql+psycopg:///{db}?host={socket}&port={port}'}
    run('focused-postgres',[PY,'-m','pytest','-q','-rs','tests/integration/db/test_execution_attempt_context.py','tests/tools/test_gateway_envelope_integrity.py','tests/integration/db/test_effect_transactions.py','tests/tools/test_v17_gateway_classification_fences.py','-p','no:cacheprovider'],pg_env)
    run('full-postgres',[PY,'-m','pytest','-q','-rs','--tb=short','-p','no:cacheprovider'],pg_env)
    with psycopg.connect(dbname=db,host=socket,port=port,autocommit=True) as c:
        pg['public_tables_after_tests']=c.execute("select count(*) from information_schema.tables where table_schema='public'").fetchone()[0]
finally:
    if pg['created']:
        with psycopg.connect(dbname='postgres',host=socket,port=port,autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db)))
            pg['cleanup_remaining']=c.execute('select count(*) from pg_database where datname=%s',(db,)).fetchone()[0]
    (out/'postgres.json').write_text(json.dumps(pg,indent=2)+'\n'); print(json.dumps(pg),flush=True)
run('blob-hashes-after',['git','hash-object',*FILES])
run('status-after',['git','status','--short'])
