import json,os,tempfile,re
from pathlib import Path
from sqlalchemy import text
from swarm.tools.permission_mission import run_permission_mission_sync
from swarm.db.engine import create_db_engine
with tempfile.TemporaryDirectory(prefix='swarm-permission-repo-') as folder:
 repo=Path(folder)
 fixture=repo/'sandbox/selfdev_issue/parser_helper.py';fixture.parent.mkdir(parents=True);fixture.write_text('synthetic permitted read\n')
 proof=run_permission_mission_sync(repo)
 print(json.dumps(proof,indent=2))
 assert proof['ok'] is True
 assert (repo/'var/tool-audit/permission_probe.txt').read_text()=='v0.5 permission mission ok\n'
 engine=create_db_engine()
 with engine.connect() as c:
  counts={table:c.execute(text('select count(*) from '+table)).scalar_one() for table in ['action_effects','action_receipts','approvals']}
  state=c.execute(text('select state from action_effects')).scalar_one()
  used=c.execute(text('select used_count from approvals')).scalar_one()
  receipt=c.execute(text('select receipt from action_receipts')).scalar_one()
  assert re.fullmatch('[0-9a-f]{64}', receipt['manifest_digest'])
  print(json.dumps({'stored_manifest_digest':receipt['manifest_digest']}))
 assert counts=={'action_effects':1,'action_receipts':1,'approvals':1},counts
 assert state=='succeeded' and used==1
 print(json.dumps({'durable_counts':counts,'state':state,'approval_used_count':used,'result':'PASS_DURABLE_PERMISSION_PATH'}))
 engine.dispose()
