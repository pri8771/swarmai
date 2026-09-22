from __future__ import annotations
import os, subprocess, sys, time
from pathlib import Path
import psycopg
repo=Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-r28c-source')
venv=Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-source/.venv/bin')
sock='/tmp/swarm-pgcheck.QxqRvZ'; port=56421
db=f'swarm_r28c_product_fixture_{os.getpid()}_{int(time.time())}'
log_path=Path('/tmp/swarm-r28c-product-fixture-green.log')
exit_code=98; remaining=1
with log_path.open('w',encoding='utf-8') as log:
 def emit(s): print(s,flush=True); log.write(s+'\n'); log.flush()
 emit('database='+db)
 command=[str(venv/'pytest'),'-q','tests/product/test_product.py::test_product_journey_proof']
 emit('command=PYTHONPATH="$PWD/src:$PWD" SWARM_DATABASE_URL="postgresql+psycopg:///'+db+'?host='+sock+'&port='+str(port)+'" '+' '.join(command))
 try:
  with psycopg.connect(dbname='postgres',host=sock,port=port,autocommit=True) as c: c.execute(f'create database "{db}"')
  env=os.environ.copy(); env['PYTHONPATH']=f'{repo / "src"}:{repo}'; env['SWARM_DATABASE_URL']=f'postgresql+psycopg:///{db}?host={sock}&port={port}'
  p=subprocess.run(command,cwd=repo,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  print(p.stdout,end='',flush=True); log.write(p.stdout); exit_code=p.returncode; emit('pytest_exit='+str(exit_code))
 finally:
  with psycopg.connect(dbname='postgres',host=sock,port=port,autocommit=True) as c:
   c.execute(f'drop database if exists "{db}" with (force)')
   remaining=c.execute('select count(*) from pg_database where datname=%s',(db,)).fetchone()[0]
  emit('cleanup_remaining='+str(remaining))
sys.exit(exit_code if remaining==0 else 99)
