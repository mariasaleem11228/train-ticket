"""Run the News module beside the deployed Go service without changing live routes."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
name = 'news-module-candidate'
existing = subprocess.check_output(['docker', 'ps', '-a', '--format', '{{.Names}}'], text=True).splitlines()
if name in existing:
    raise RuntimeError(f'{name} already exists; inspect and remove it explicitly before restarting')
host = json.loads(subprocess.check_output(
    ['docker', 'inspect', 'station-migration-modulith-1'], text=True))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env.update(NEWS_ENABLED='true', MODULITH_OWNERSHIP_FILE='')
path = root / 'ts-modulith/target/news-candidate.env'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key, value in env.items()), encoding='utf-8')
subprocess.run(['docker', 'run', '-d', '--name', name, '--network', 'train-ticket_my-network',
                '-p', '127.0.0.1:18129:18080', '--env-file', str(path),
                'train-ticket/ts-modulith:news-candidate'], check=True)
print('News candidate started on http://127.0.0.1:18129; live routes unchanged')
