"""Start a read-only Route Plan candidate beside the live hybrid host."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
name = 'station-migration-route-plan-candidate-1'
image = 'train-ticket/ts-modulith:route-plan-candidate'
host = json.loads(subprocess.check_output(
    ['docker', 'inspect', 'station-migration-modulith-1'], text=True))[0]
environment = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
environment['ROUTE_PLAN_ENABLED'] = 'true'
for key in tuple(environment):
    if key.endswith('_WRITES_ENABLED'):
        environment[key] = 'false'
path = root / 'ts-modulith/target/route-plan-candidate.env'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key,value in environment.items()), encoding='utf-8')
existing = subprocess.check_output(['docker', 'ps', '-a', '--format', '{{.Names}}'], text=True).splitlines()
if name in existing:
    subprocess.run(['docker', 'rm', '-f', name], check=True, capture_output=True)
subprocess.run(['docker', 'run', '-d', '--name', name, '--network',
                'train-ticket_my-network', '-p', '127.0.0.1:18102:18080',
                '--env-file', str(path), image], check=True, capture_output=True)
print('Route Plan candidate started on http://127.0.0.1:18102')
