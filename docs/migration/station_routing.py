"""Install/switch/restore the Station strangler on the existing local Docker network.

Usage: python docs/migration/station_routing.py install|module|legacy|restore|status
Switches deliberately use a brief maintenance response while ownership changes.
The original service and volumes are retained. State is in deployment/migration/.state.
Do not run root docker compose up while this service's network identity is moved.
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from http_support import request, wait_ready

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'deployment/migration/.state/routing-state.json'
CONFIG = STATE.parent / 'routing'
EVIDENCE = ROOT / 'ts-modulith/target/evidence'
ORIGINAL = 'train-ticket-ts-station-service-1'
PROXY = 'station-migration-proxy'
MODULE = 'station-migration-modulith-1'
LEGACY = 'station-migration-station-legacy-1'
COMPOSE = ['compose', '-p', 'station-migration', '-f', str(ROOT / 'deployment/migration/compose.station.yml')]

def docker(*args, env=None):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, check=True, env=env)
    return result.stdout.strip()

def inspect(name):
    return json.loads(docker('inspect', name))[0]

def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')

def configure(mode, reload=True):
    CONFIG.mkdir(parents=True, exist_ok=True)
    if mode == 'maintenance':
        location = 'return 503;'
    else:
        target = 'ts-modulith:18080' if mode == 'module' else 'station-legacy:12345'
        location = f'''resolver 127.0.0.11 valid=5s ipv6=off;
        set $backend http://{target};
        proxy_pass $backend$request_uri;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;'''
    (CONFIG / 'default.conf').write_text(f'''server {{
    listen 12345;
    add_header X-Station-Backend "{mode}" always;
    location / {{ {location} }}
}}
''', encoding='utf-8')
    if reload:
        docker('exec', PROXY, 'nginx', '-t')
        docker('exec', PROXY, 'nginx', '-s', 'reload')
        # Allow old workers to drain before stopping their authoritative backend.
        time.sleep(2)

def wait_container(name, module=False):
    deadline = time.monotonic() + 180
    path = '/api/v1/stationservice/stations'
    while time.monotonic() < deadline:
        try:
            ip = next(iter(inspect(name)['NetworkSettings']['Networks'].values()))['IPAddress']
            # Probe from the proxy's network; containers need no extra published ports.
            port = '18080' if module else '12345'
            body = docker('exec', PROXY, 'wget', '-qO-', f'http://{ip}:{port}{path}')
            if json.loads(body).get('status') == 1:
                return
        except (subprocess.CalledProcessError, ValueError, KeyError):
            pass
        print('Waiting for', name, flush=True)
        time.sleep(3)
    raise RuntimeError('Backend not ready: ' + name)

def restore(state):
    # Release the retained IP/port before returning it to the original container.
    names = docker('ps', '-a', '--format', '{{.Names}}').splitlines()
    if PROXY in names:
        docker('stop', '-t', '30', PROXY)
        docker('rm', PROXY)
    for name in [MODULE, LEGACY]:
        if name in names:
            docker('stop', '-t', '30', name)
    current = inspect(ORIGINAL)['NetworkSettings']['Networks']
    if state['network'] not in current:
        docker('network', 'connect', '--ip', state['ip'], '--alias', 'ts-station-service', state['network'], ORIGINAL)
    docker('update', '--restart=' + state.get('restart_policy', 'always'), ORIGINAL)
    docker('start', ORIGINAL)
    wait_ready('http://127.0.0.1:12345')
    state['mode'] = 'restored'
    save(state)

def install():
    if STATE.exists() and json.loads(STATE.read_text())['mode'] != 'restored':
        raise RuntimeError('Routing already installed. Use status/module/legacy/restore.')
    contracts = json.loads((EVIDENCE / 'station-contracts.json').read_text(encoding='utf-8'))
    if len(contracts) < 32 or not all(r['passed'] for r in contracts):
        raise RuntimeError('Run the isolated contract suite successfully before installing routing.')
    if not (EVIDENCE / 'station-backup.archive').exists():
        raise RuntimeError('Station data backup is required.')
    original = inspect(ORIGINAL)
    if original['State']['Status'] != 'running':
        raise RuntimeError('Original Station must be running.')
    networks = original['NetworkSettings']['Networks']
    if len(networks) != 1:
        raise RuntimeError('Expected one legacy network; inspect topology first.')
    network, settings = next(iter(networks.items()))
    policy = original['HostConfig']['RestartPolicy']
    restart = policy['Name']
    if restart == 'on-failure' and policy.get('MaximumRetryCount'):
        restart += ':' + str(policy['MaximumRetryCount'])
    state = {'original': ORIGINAL, 'network': network, 'ip': settings['IPAddress'],
             'image': original['Image'], 'aliases': settings['Aliases'], 'mode': 'installing'}
    state['restart_policy'] = restart
    save(state)
    try:
        configure('maintenance', reload=False)
        docker('update', '--restart=no', ORIGINAL)
        docker('stop', '-t', '30', ORIGINAL)
        docker('network', 'disconnect', network, ORIGINAL)
        docker('run', '-d', '--name', PROXY, '--restart', 'unless-stopped', '--network', network, '--ip', state['ip'],
               '--network-alias', 'ts-station-service', '-p', '12345:12345',
               '--mount', f'type=bind,source={CONFIG},target=/etc/nginx/conf.d,readonly',
               'nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10')
        docker(*COMPOSE, '--profile', 'routing', 'up', '-d', 'station-legacy')
        wait_container(LEGACY)
        configure('legacy')
        wait_ready('http://127.0.0.1:12345')
        state['mode'] = 'legacy'
        save(state)
    except Exception:
        restore(state)
        raise

def switch(mode):
    state = json.loads(STATE.read_text())
    if state['mode'] == 'restored':
        raise RuntimeError('Install routing first.')
    configure('maintenance')
    state['mode'] = 'maintenance'
    save(state)
    try:
        if mode == 'module':
            docker('stop', '-t', '30', LEGACY)
            env = dict(os.environ, STATION_WRITES_ENABLED='true')
            docker(*COMPOSE, 'up', '-d', 'modulith', env=env)
            wait_container(MODULE, module=True)
        else:
            docker('stop', '-t', '30', MODULE)
            docker(*COMPOSE, '--profile', 'routing', 'up', '-d', 'station-legacy')
            wait_container(LEGACY)
        configure(mode)
        wait_ready('http://127.0.0.1:12345')
        state['mode'] = mode
        save(state)
    except Exception:
        # A failed switch returns to the untouched original deployment.
        restore(state)
        raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'module', 'legacy', 'restore', 'status'])
    args = parser.parse_args()
    if (STATE.parent / 'hybrid.json').exists():
        # After a second module joins the host, Station rollback must not stop it.
        import hybrid_routing
        if args.action in ('module', 'legacy'):
            hybrid_routing.switch('station', args.action)
        elif args.action == 'restore':
            hybrid_routing.restore('station')
        elif args.action == 'install':
            raise RuntimeError('Use the shared hybrid routing runbook after stage 2.')
        print(STATE.read_text())
        raise SystemExit(0)
    if args.action == 'install':
        install()
    elif args.action in ('module', 'legacy'):
        switch(args.action)
    elif args.action == 'restore':
        restore(json.loads(STATE.read_text()))
    print(STATE.read_text() if STATE.exists() else 'Routing not installed')
