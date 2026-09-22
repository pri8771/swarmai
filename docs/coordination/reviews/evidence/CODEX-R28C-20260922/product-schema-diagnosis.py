from __future__ import annotations
import json, os, subprocess, sys, tempfile, time
from pathlib import Path
import psycopg

repo=Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-r28c-source')
venv=Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-source/.venv/bin')
sock='/tmp/swarm-pgcheck.QxqRvZ'; port=56421
log_path=Path('/tmp/swarm-r28c-product-schema-diagnosis.log')
base_env=os.environ.copy(); base_env['PYTHONPATH']=f'{repo / "src"}:{repo}'
base_env.pop('SWARM_LIVE_LOCAL',None)

def emit(log,s):
 print(s,flush=True); log.write(s+'\n'); log.flush()

def run(log,cmd,env):
 emit(log,'COMMAND='+' '.join(cmd))
 p=subprocess.run(cmd,cwd=repo,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 print(p.stdout,end='',flush=True); log.write(p.stdout); log.flush(); emit(log,f'EXIT={p.returncode}')
 return p.returncode

helper=Path('/tmp/swarm-r28c-run-permission-direct.py')
helper.write_text('''import asyncio, json, os, tempfile\nfrom pathlib import Path\nfrom sqlalchemy import create_engine, inspect, text\nfrom swarm.tools.permission_mission import run_permission_mission\nroot=Path(tempfile.mkdtemp(prefix="swarm-r28c-permission-repo-"))\n(root/"sandbox/selfdev_issue").mkdir(parents=True)\n(root/"sandbox/selfdev_issue/parser_helper.py").write_text("def add(a,b):\\n    return a+b\\n")\nresult=asyncio.run(run_permission_mission(root))\nprint("PERMISSION_RESULT="+json.dumps(result,sort_keys=True,default=str))\neng=create_engine(os.environ["SWARM_DATABASE_URL"])\nnames=set(inspect(eng).get_table_names())\ncounts={}\nwith eng.connect() as c:\n for table in ("missions","task_attempts","worker_leases","approvals","action_effects","action_receipts"):\n  counts[table]=c.execute(text(f"select count(*) from {table}")).scalar() if table in names else "missing"\nprint("TABLE_COUNTS="+json.dumps(counts,sort_keys=True))\neng.dispose()\n''',encoding='utf-8')

with log_path.open('w',encoding='utf-8') as log:
 emit(log,'HEAD='+subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip())
 emit(log,'TREE='+subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=repo,text=True).strip())
 for label,migrated in [('empty',False),('migrated',True)]:
  db=f'swarm_r28c_product_{label}_{os.getpid()}_{int(time.time())}'
  env=base_env.copy(); env['SWARM_DATABASE_URL']=f'postgresql+psycopg:///{db}?host={sock}&port={port}'
  emit(log,f'CASE={label} DATABASE={db}')
  try:
   with psycopg.connect(dbname='postgres',host=sock,port=port,autocommit=True) as c: c.execute(f'create database "{db}"')
   if migrated:
    run(log,[str(venv/'alembic'),'-c',str(repo/'alembic.ini'),'upgrade','head'],env)
   run(log,[str(venv/'python'),str(helper)],env)
   run(log,[str(venv/'pytest'),'-q','tests/product/test_product.py::test_product_journey_proof'],env)
  finally:
   with psycopg.connect(dbname='postgres',host=sock,port=port,autocommit=True) as c:
    c.execute(f'drop database if exists "{db}" with (force)')
    remain=c.execute('select count(*) from pg_database where datname=%s',(db,)).fetchone()[0]
   emit(log,f'CASE={label} cleanup_remaining={remain}')
