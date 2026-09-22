from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import psycopg

repo = Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-r28c-source')
venv = Path('/Users/pchordia/Downloads/swarm_codex/review/swarm-source/.venv/bin')
socket = '/tmp/swarm-pgcheck.QxqRvZ'
port = 56421
db = f'swarm_r28c_network_{os.getpid()}_{int(time.time())}'
log_path = Path(sys.argv[1])
targets = sys.argv[2:]

pytest_command = (
    f'PYTHONPATH="$PWD/src:$PWD" SWARM_DATABASE_URL='
    f'"postgresql+psycopg:///{db}?host={socket}&port={port}" '
    f'{venv / "pytest"} -q ' + ' '.join(targets)
)
result_code = 98
cleanup_remaining = None
with log_path.open('w', encoding='utf-8') as log:
    def record(line: str) -> None:
        print(line, flush=True)
        log.write(line + '\n')
        log.flush()

    record(f'repo={repo}')
    record(f'database={db}')
    record(f'command={pytest_command}')
    try:
        with psycopg.connect(dbname='postgres', host=socket, port=port, autocommit=True) as conn:
            conn.execute(f'CREATE DATABASE "{db}"')
        record('database_create_exit=0')
        env = os.environ.copy()
        env['PYTHONPATH'] = f'{repo / "src"}:{repo}'
        env['SWARM_DATABASE_URL'] = f'postgresql+psycopg:///{db}?host={socket}&port={port}'
        command = [str(venv / 'pytest'), '-q', *targets]
        proc = subprocess.run(command, cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.write(proc.stdout)
        log.flush()
        print(proc.stdout, end='', flush=True)
        result_code = proc.returncode
        record(f'pytest_exit={result_code}')
    finally:
        with psycopg.connect(dbname='postgres', host=socket, port=port, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')
            cleanup_remaining = conn.execute('SELECT count(*) FROM pg_database WHERE datname=%s', (db,)).fetchone()[0]
        record(f'cleanup_remaining={cleanup_remaining}')

sys.exit(result_code if cleanup_remaining == 0 else 99)
