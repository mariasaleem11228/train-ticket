"""Run the Ticket Office module against its own MongoDB snapshot."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
name = 'ticket-office-module-candidate'
existing = subprocess.check_output(['docker', 'ps', '-a', '--format', '{{.Names}}'], text=True).splitlines()
if name in existing:
    raise RuntimeError(f'{name} already exists; inspect it before restarting')
host = json.loads(subprocess.check_output(
    ['docker', 'inspect', 'station-migration-modulith-1'], text=True))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env.update(TICKET_OFFICE_ENABLED='true', TICKET_OFFICE_WRITES_ENABLED='true',
           TICKET_OFFICE_MONGO_URI='mongodb://ticket-office-mongo-candidate:27017/office_module',
           MODULITH_OWNERSHIP_FILE='')
path = root / 'ts-modulith/target/ticket-office-candidate.env'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key, value in env.items()), encoding='utf-8')
subprocess.run(['docker', 'run', '-d', '--name', name, '--network', 'train-ticket_my-network',
                '-p', '127.0.0.1:18130:18080', '--env-file', str(path),
                'train-ticket/ts-modulith:ticket-office-candidate'], check=True)
print('Ticket Office module candidate started; live routes unchanged')
