"""Configure existing local containers without replacing volumes or network IDs.

External Spring properties override bundled defaults. Refuse to replace an
existing unrelated file. Backups/state remain under deployment/migration/.state.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'deployment/migration/messaging.properties'
STATE = ROOT / 'deployment/migration/.state/messaging'
SERVICES = ['preserve', 'preserve-other', 'food', 'notification']
STATE.mkdir(parents=True, exist_ok=True)

def docker(*args):
    return subprocess.check_output(['docker', *args], text=True).strip()

docker('compose', '-p', 'migration-infra', '-f', str(ROOT / 'deployment/migration/compose.infrastructure.yml'), 'up', '-d')
report = []
for service in SERVICES:
    name = f'train-ticket-ts-{service}-service-1'
    original = json.loads(docker('inspect', name))[0]
    file_exists = subprocess.run(['docker', 'exec', name, 'test', '-f', '/config/application.properties'], capture_output=True).returncode == 0
    if file_exists:
        existing = docker('exec', name, 'cat', '/config/application.properties')
        if not existing.startswith('# Local benchmark infrastructure. No external SMTP deliveries.'):
            raise RuntimeError('Existing unrelated configuration: ' + name)
        (STATE / (service + '-previous.properties')).write_text(existing,encoding='utf-8')
    docker('exec', name, 'mkdir', '-p', '/config')
    docker('cp', str(SOURCE), name + ':/config/application.properties')
    docker('restart', '-t', '30', name)
    now = json.loads(docker('inspect', name))[0]
    old_ips = {key: value['IPAddress'] for key, value in original['NetworkSettings']['Networks'].items()}
    new_ips = {key: value['IPAddress'] for key, value in now['NetworkSettings']['Networks'].items()}
    assert old_ips == new_ips, (name, old_ips, new_ips)
    report.append({'container': name, 'ips': new_ips, 'previous_external_config': file_exists})
    (STATE / 'applied.json').write_text(json.dumps(report, indent=2))
    print('Configured and restarted:', name, flush=True)
