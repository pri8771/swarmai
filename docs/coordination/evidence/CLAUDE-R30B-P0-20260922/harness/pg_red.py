import json, os, subprocess, time, sys
from pathlib import Path
import psycopg
from psycopg import sql
PY='/private/tmp/swarm-r28d3-repair-20260922/.venv/bin/python'
repo=Path('/tmp/swarm-astra-r30b-p0-resume-20260922/baseline-6dbf8c4'); out=Path('/tmp/swarm-astra-r30b-p0-resume-20260922')
env=os.environ.copy(); env['PYTHONPATH']=f'{repo/"src"}:{repo}'; env['SWARM_ALLOW_PAID']='false'; env['SWARM_LIVE_LOCAL']='0'; env.pop('SWARM_DATABASE_URL',None)
socket='/tmp/swarm-pgcheck.QxqRvZ'; port=56421; db=f'swarm_r30b_p0_{os.getpid()}_{int(time.time())}'
pg={'socket':socket,'port':port,'database':db,'created':False}
tests=sys.argv[1:] or ['tests/integration/db/test_execution_attempt_context.py','tests/tools/test_gateway_envelope_integrity.py','tests/integration/db/test_effect_transactions.py']
try:
    with psycopg.connect(dbname='postgres',host=socket,port=port,autocommit=True) as c:
        pg['current_user']=c.execute('select current_user').fetchone()[0]
        for k in ['data_directory','port','listen_addresses']:
            pg[k]=c.execute(sql.SQL('SHOW {}').format(sql.Identifier(k))).fetchone()[0]
        assert pg['current_user']=='pchordia' and pg['data_directory']=='/tmp/swarm-pgcheck.QxqRvZ/data' and pg['port']=='56421' and pg['listen_addresses']==''
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db))); pg['created']=True
    pg_env=env|{'SWARM_DATABASE_URL':f'postgresql+psycopg:///{db}?host={socket}&port={port}'}
    p=subprocess.run([PY,'-m','pytest','-q','-rs',*tests],cwd=repo,env=pg_env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'pg-red-baseline.log').write_text(p.stdout); pg['exit']=p.returncode; print(p.stdout[-5000:])
finally:
    if pg['created']:
        with psycopg.connect(dbname='postgres',host=socket,port=port,autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db)))
            pg['cleanup_remaining']=c.execute('select count(*) from pg_database where datname=%s',(db,)).fetchone()[0]
    (out/'pg-red-baseline.json').write_text(json.dumps(pg,indent=2)); print(json.dumps(pg))
