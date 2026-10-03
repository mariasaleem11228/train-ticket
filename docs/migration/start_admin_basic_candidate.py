"""Run Admin Basic Info beside legacy with provider writes disabled."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
host = json.loads(subprocess.check_output(
    ['docker', 'inspect', 'station-migration-modulith-1'], text=True))[0]
env = dict(item.split('=', 1) for item in host['Config']['Env'] if '=' in item)
for key in env:
    if key.endswith('_WRITES_ENABLED'):
        env[key] = 'false'
env.update(ADMIN_BASIC_ENABLED='true', MODULITH_OWNERSHIP_FILE='')
file = root / 'ts-modulith/target/admin-basic-candidate.env'
file.write_text(''.join(key+'='+value+'\n' for key, value in env.items()), encoding='utf-8')
subprocess.run(['docker', 'run', '-d', '--name', 'admin-basic-module-candidate',
                '--network', 'train-ticket_my-network', '-p', '127.0.0.1:18123:18080',
                '--env-file', str(file), 'train-ticket/ts-modulith:admin-basic-candidate'], check=True)
print('Admin Basic Info read-only candidate launched on port 18123')
