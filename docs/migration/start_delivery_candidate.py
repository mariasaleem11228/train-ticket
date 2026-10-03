"""Start Delivery against its isolated queue and database; live messages stay untouched."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
name = 'delivery-module-candidate'
existing = subprocess.check_output(['docker', 'ps', '-a', '--format', '{{.Names}}'], text=True).splitlines()
if name in existing:
    raise RuntimeError(f'{name} already exists; inspect and remove it explicitly before restarting')
host = json.loads(subprocess.check_output(
    ['docker', 'inspect', 'station-migration-modulith-1'], text=True))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env.update(DELIVERY_ENABLED='true', DELIVERY_WRITES_ENABLED='true',
           DELIVERY_QUEUE='food_delivery_candidate',
           DELIVERY_JDBC_URL='jdbc:mysql://ts-delivery-mysql:3306/delivery_candidate',
           DELIVERY_DB_USER='root', DELIVERY_DB_PASSWORD='root',
           MODULITH_OWNERSHIP_FILE='')
path = root / 'ts-modulith/target/delivery-candidate.env'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(''.join(f'{key}={value}\n' for key, value in env.items()), encoding='utf-8')
subprocess.run(['docker', 'run', '-d', '--name', name, '--network', 'train-ticket_my-network',
                '-p', '127.0.0.1:18141:18080', '--env-file', str(path),
                'train-ticket/ts-modulith:delivery-candidate'], check=True)
print('Delivery candidate started; queue food_delivery_candidate, database delivery_candidate')
