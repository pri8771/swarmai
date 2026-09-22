import os,json,subprocess,uuid
from pathlib import Path
import psycopg
from psycopg import sql
source=Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-r29a-source')
venv=source.parent/'swarm-source/.venv/bin'
name='swarm_r29a_permission_'+uuid.uuid4().hex[:10]
out=Path('/tmp/swarm-r29a-permission-final-evidence');out.mkdir(exist_ok=True)
env={**os.environ,'PYTHONPATH':str(source/'src')+':'+str(source),'SWARM_DATABASE_URL':f'postgresql+psycopg:///{name}?host=/tmp/swarm-pgcheck.QxqRvZ&port=56421'}
run={'database':name,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'provisional_uncommitted':False,'source_tree':'1b8577c91b2984b804ea6df259e6a47a697ccc31'}
assert run['source_head']=='1ea1ca55a2470d94fe704d64c029a991c3c0dea5'
assert subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=source,text=True).strip()==run['source_tree']
assert subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True)==''
with psycopg.connect(dbname='postgres',host='/tmp/swarm-pgcheck.QxqRvZ',port=56421,autocommit=True) as c:
 c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
 try:
  for label,cmd in [('migration',[str(venv/'alembic'),'upgrade','head']),('workflow',[str(venv/'python'),'/tmp/swarm-r29a-permission-pg.py'])]:
   with (out/(label+'.log')).open('w') as log:
    p=subprocess.run(cmd,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT)
   run[label+'_exit']=p.returncode
   assert p.returncode==0,(label,(out/(label+'.log')).read_text()[-3000:])
 finally:
  c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
  run['cleanup_remaining']=c.execute('select count(*) from pg_database where datname=%s',(name,)).fetchone()[0]
  (out/'run.json').write_text(json.dumps(run,indent=2))
  print(json.dumps(run))
