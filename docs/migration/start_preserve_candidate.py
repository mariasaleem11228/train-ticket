"""Start Preserve on an isolated Orders database for booking comparisons."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
name = 'station-migration-preserve-candidate-1'
image = 'train-ticket/ts-modulith:preserve-candidate'
host = json.loads(subprocess.check_output(
    ['docker', 'inspect', 'station-migration-modulith-1'], text=True))[0]
environment = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in tuple(environment):
    if key.endswith('_WRITES_ENABLED'):
        environment[key] = 'false'
environment['PRESERVE_ENABLED'] = 'true'
environment['PRESERVE_WRITES_ENABLED'] = 'true'
environment['ORDER_WRITES_ENABLED'] = 'true'
environment['ORDER_MONGO_URI'] = 'mongodb://ts-order-mongo:27017/preserve_module_migration_test'
environment.pop('MODULITH_OWNERSHIP_FILE', None)
path = root / 'ts-modulith/target/preserve-candidate.env'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key,value in environment.items()), encoding='utf-8')
existing = subprocess.check_output(['docker', 'ps', '-a', '--format', '{{.Names}}'], text=True).splitlines()
if name in existing:
    subprocess.run(['docker', 'rm', '-f', name], check=True, capture_output=True)
subprocess.run(['docker', 'run', '-d', '--name', name, '--network',
                'train-ticket_my-network', '-p', '127.0.0.1:18106:18080',
                '--env-file', str(path), image], check=True, capture_output=True)
print('Isolated Preserve candidate started on http://127.0.0.1:18106')
